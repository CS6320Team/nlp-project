import json
import os
from typing import Dict, Any

import chess
import stockfish
import torch
from dotenv import load_dotenv
from langchain.prompts import ChatPromptTemplate
from langchain.schema import HumanMessage, SystemMessage
from langchain_openai import ChatOpenAI
from transformers import AutoTokenizer, AutoModelForCausalLM, PreTrainedModel


class ChessCoach:
    def __init__(self, stockfish_path: str, openai_api_key: str, openai_model: str, chess_model: str):
        os.environ["OPENAI_API_KEY"] = openai_api_key

        self.stockfish = stockfish.Stockfish(path=stockfish_path)

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

    def generate_commentary(self, board_fen: str, prev_board_fen: str) -> str:
        input_text = (
            f"An insightful and helpful Chess Assistant giving commentary on chess moves through FEN notation.<|endoftext|>"
            f"Current FEN: {board_fen}<|endoftext|>"
            f"Previous FEN: {prev_board_fen}<|endoftext|>"
            f"Commentary: ")

        inputs = self.commentary_tokenizer(input_text, return_tensors='pt').to(self.chess_model.device)
        input_length = inputs.input_ids.shape[1]

        outputs = self.chess_model.generate(
            **inputs, max_new_tokens=256, do_sample=True, temperature=0.7, top_p=0.7, top_k=50,
            return_dict_in_generate=True,
            pad_token_id=self.commentary_tokenizer.eos_token_id,
        )

        # Decode and return commentary
        token = outputs.sequences[0, input_length:]
        commentary = self.commentary_tokenizer.decode(token, skip_special_tokens=True)

        # todo: refine commentary

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

    def process_user_input(self, user_input: str) -> Dict[str, Any]:
        """
        Main method to process user input and generate appropriate response
        """
        # Classify input
        classification = self.classify_input(user_input)

        # Current board FEN for context
        current_board_fen = self.board.fen()

        # Process based on classification type
        if classification['type'] == 'make_move':
            try:
                # Attempt to make the move (# todo: use chess model (openai responds with something like "User wans to move ther pawn to e4, needs to be converted to UCI based on current board state"))

                # Parse the move (#todo need to use chess model)
                parse_prompt = ChatPromptTemplate.from_messages([
                    SystemMessage(
                        content=f"You are a chess AI assistant. You will be given current FEN string, Parse the next move to UCI format. Use standard chess notation"),
                    HumanMessage(content=f"Make the move: {classification['context']}. "
                                         f"Current Board Position: {current_board_fen}. "
                                         f"Respond in strictly in UCI format / Standard Chess Notation.")
                ])
                response = self.classification_llm.invoke(parse_prompt.messages).content

                move = chess.Move.from_uci(response)
                if move in self.board.legal_moves:
                    self.board.push(move)
                    self.prev_board_fen = current_board_fen

                    response = f"Move {move} executed successfully."
                else:
                    response = "Illegal move. Please try again."
            except ValueError:
                response = "Invalid move format. Use standard chess notation."
        elif classification['type'] == 'give_insight':
            # todo: ...
            response = self.generate_commentary(current_board_fen, self.prev_board_fen)
        elif classification['type'] == 'best_move':
            best_move = self.get_best_move(current_board_fen)
            response = f"Stockfish suggests the best move: {best_move}"
        elif classification['type'] == 'ask_question':
            # Refine question with board context # todo: use chess model instead of openai
            question_prompt = ChatPromptTemplate.from_messages([
                # todo: needs better system message
                SystemMessage(content=f"Current Board Position: {current_board_fen}"),
                HumanMessage(
                    content=f"In 75 words on less, provide a chess-related answer to: {classification['context']}")
            ])

            response = self.refinement_llm.invoke(question_prompt.messages).content

        else:  # general conversation (# todo: use chess model)
            conversation_prompt = ChatPromptTemplate.from_messages([
                SystemMessage(
                    content="You are a chess AI assistant. Keep the conversation focused on chess. Respond with 75 words or less."),
                HumanMessage(content=user_input)
            ])
            response = self.refinement_llm.invoke(conversation_prompt.messages).content

        return {
            "type": classification['type'],
            "response": response
        }


def main():
    load_dotenv()

    # todo: use config
    assistant = ChessCoach(
        stockfish_path="C:/stockfish/stockfish-windows-x86-64-avx2.exe",
        openai_api_key=os.getenv("OPENAI_API_KEY"),
        openai_model="gpt-4o-mini",
        chess_model="Waterhorse/chessgpt-chat-v1"
    )

    player_name = input("Enter player name: ")
    player_elo = int(input("Enter player ELO: "))

    # Generate greeting
    greeting = assistant.generate_greeting(player_name, player_elo)
    print(greeting)

    while True:
        user_input = input("User: ")
        response = assistant.process_user_input(user_input)
        print("Chess Coach:" + response['response'])


if __name__ == "__main__":
    main()
