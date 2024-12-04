import json
import os
from typing import Dict

import chess
import torch
from langchain.prompts import ChatPromptTemplate
from langchain.schema import HumanMessage, SystemMessage
from langchain_openai import ChatOpenAI
from stockfish import Stockfish
from transformers import AutoTokenizer, AutoModelForCausalLM, PreTrainedModel


class ChessCoach:
    def __init__(self, stockfish: Stockfish, openai_api_key: str, openai_model: str, chess_model: str):
        os.environ["OPENAI_API_KEY"] = openai_api_key

        self.stockfish = stockfish

        # Initialize OpenAI models (#todo: could prob just use 1)
        self.classification_llm = ChatOpenAI(model=openai_model)
        self.refinement_llm = ChatOpenAI(model=openai_model)

        self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")

        # Initialize Commentary Model
        self.commentary_tokenizer = AutoTokenizer.from_pretrained(chess_model)
        self.chess_model: PreTrainedModel = AutoModelForCausalLM.from_pretrained(chess_model, torch_dtype=torch.float16)
        self.chess_model.to(self.device)

        # Chess board representation
        self.board = chess.Board()
        self.prev_board_fen = self.board.fen()

    def generate_greeting(self, player_name: str, player_elo: int) -> str:
        """Generate a personalized greeting based on player details"""
        greeting_prompt = ChatPromptTemplate.from_messages([
            SystemMessage(
                content="You are a chess AI assistant generating a unique greeting. You are capable of analyzing chess games and providing insights."),
            HumanMessage(
                content=f"Generate a personalized chess greeting and mention your capabilities in strictly 50 words or less. Player Name: {player_name}, Player ELO: {player_elo}")
        ])

        response = self.classification_llm.invoke(greeting_prompt.messages)
        return response.content

    def classify_input(self, user_input: str) -> Dict[str, str]:
        """
        Use OpenAI to classify user input into chess-related categories
        Supported categories: make_move, give_insight, ask_question, general_convo, best_move
        """

        # todo: give_insight is probably not a good representation for just commentary
        classification_prompt = ChatPromptTemplate.from_messages([
            SystemMessage(content="""
            You are an expert chess AI classifier. Classify the user input into one of these categories:
            - make_move: User wants to make a specific chess move
            - give_insight: User wants analysis or commentary on the current game state
            - ask_question: User is asking a specific chess-related question
            - general_convo: User wants to have a general chat about chess
            - best_move: User wants to know the best possible move in the current position

            Respond strictly in the following JSON format:
            {
                "type": "<classified_type>",
                "context": "<type_specific_context>"
            }
            """),
            HumanMessage(content=f"Classify this input: {user_input}")
        ])

        response = self.classification_llm.invoke(classification_prompt.messages)

        try:
            return json.loads(response.content)
        except json.JSONDecodeError:  # Fallback classification
            return {
                "type": "general_convo",
                "context": user_input
            }

    def generate_commentary(self, board_fen: str, prev_board_fen: str, move: str) -> str:
        input_text = (
            f"An insightful chess commentator observing chess game between two players and making commentary by looking at current and previous state of chess board fen notation.<|endoftext|>"
            f"Current FEN: {board_fen}<|endoftext|>"
            f"Previous FEN: {prev_board_fen}<|endoftext|>"
            f"Move made: {move}<|endoftext|>"
            f"Chess Commentator's commentary: "
        )

        inputs = self.commentary_tokenizer(input_text, return_tensors='pt').to(self.chess_model.device)
        input_length = inputs.input_ids.shape[1]

        outputs = self.chess_model.generate(
            **inputs, max_new_tokens=96, do_sample=True, temperature=0.7, top_p=0.7, top_k=50,
            return_dict_in_generate=True,
            pad_token_id=self.commentary_tokenizer.eos_token_id,
        )

        # Decode and return commentary
        token = outputs.sequences[0, input_length:]
        commentary = self.commentary_tokenizer.decode(token, skip_special_tokens=True)

        refine_prompt = ChatPromptTemplate.from_messages([
            SystemMessage(
                content="You are a chess AI assistant. You will be given a chess commentary, board states, and moves."
                        "Refine the commentary to be more insightful and engaging. "
                        "Respond with 75 words or less."),
            HumanMessage(content=f"Current FEN: {board_fen}. "
                                 f"Previous FEN: {prev_board_fen}. "
                                 f"Move made: {move}. "
                                 f"Commentary: {commentary}")
        ])
        commentary = self.refinement_llm.invoke(refine_prompt.messages).content
        return commentary

    def get_best_move(self, board_fen: str) -> str:
        """
        Get the best move from Stockfish for a given board position
        """
        # Configure Stockfish with the board position
        self.stockfish.set_fen_position(board_fen)

        # Get the best move
        best_move = self.stockfish.get_best_move()

        return best_move

    def process_make_move(self, fen, context: str, turn: str) -> chess.Move | None:
        try:
            # Attempt to make the move (# todo: use chess model (openai responds with something like "User wans to move ther pawn to e4, needs to be converted to UCI based on current board state"))

            # Parse the move (#todo need to use chess model)
            parse_prompt = ChatPromptTemplate.from_messages([
                SystemMessage(
                    content=f"You are a chess AI assistant. You will be given current FEN string, Parse the next move to UCI format. Use standard chess notation"),
                HumanMessage(content=f"Parse the move: {context}. "
                                     f"Current Board Position (FEN Notation): {fen}. "
                                     f"It is {turn}'s turn to move."
                                     f"Respond in strictly in UCI format with chess move and nothing else.")
            ])
            response = self.classification_llm.invoke(parse_prompt.messages).content
            move = chess.Move.from_uci(response)
            return move
        except ValueError:
            return None

    def process_question(self, current_fen, context: str, user: str, elo: int) -> str:
        question_prompt = ChatPromptTemplate.from_messages([
            # todo: use commentary as context
            SystemMessage(content=f"You are a chess expert and a coach. "
                                  f"Your student is {user} with an ELO rating of {elo}. "
                                  f"Current Board Position: {current_fen}"),
            HumanMessage(
                content=f"In 75 words on less, provide a chess-related answer to: '{context}' based on the current board position.")
        ])
        response = self.refinement_llm.invoke(question_prompt.messages).content
        return response

    def process_general_convo(self, user_input: str) -> str:
        conversation_prompt = ChatPromptTemplate.from_messages([
            SystemMessage(
                content="You are a chess AI assistant. Keep the conversation focused on chess. Respond with 75 words or less."),
            HumanMessage(content=user_input)
        ])
        response = self.refinement_llm.invoke(conversation_prompt.messages).content
        return response
