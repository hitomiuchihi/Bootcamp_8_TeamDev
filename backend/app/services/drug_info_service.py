import os
import logging
import aiohttp
import asyncio
from openai import OpenAI
from sqlalchemy.orm import Session
from app.database import SessionLocal, init_db
from app.models import ConversationHistory
import asyncio
from .get_user_conversation import get_user_conversation_history

# ロガーの設定
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# APIキーを設定
api_key = os.getenv("OPENAI_API_KEY")

# グローバル変数の定義
drug_name = "ロキソプロフェン"
info_type = "使い方"
pmda_url = "https://www.pmda.go.jp/PmdaSearch/iyakuSearch/"

# データベースセッションの取得：データベースの操作を行うためのセッション
# def get_db_session() -> Session:
#     return SessionLocal()

# 会話履歴を取得する関数
# def get_user_conversation_history(db: Session, user_id: str):
#     return db.query(ConversationHistory).filter(ConversationHistory.user_id == user_id).all()

# プロンプトを生成する関数
def generate_prompt(drug_name: str, info_type: str, pmda_url: str) -> str:
    logger.info(f"💊Generating prompt for drug: {drug_name}, info type: {info_type}")
    return (f"薬剤名: {drug_name}\n"
            f"知りたい情報: {info_type}\n"
            f"以下のPMDAのURLから得られる情報を参考にして、薬についてユーザーにわかりやすい説明をしてください。\n"
            f"URL: {pmda_url}")

# useridで会話履歴を取得する処理
# async def get_conversation_history(user_id):
#     # user_id = "Ufcb5e01230d0a1f9bbac8dbd9c1310d8"
#     try:
#         async with aiohttp.ClientSession() as session:
#             async with session.get(f"http://localhost:8000/api/conversation/{user_id}", timeout=10) as response:
#                 if response.status == 200:
#                     logger.info("🙆会話履歴が正常に取得されました。")
#                     data = await response.json()
#                     logger.info(f"◆ 会話履歴: {data}")
#                     return data
#                 else:
#                     logger.error(f"🙅会話履歴の取得に失敗しました: {response.status} - {await response.text()}")
#     except Exception as e:
#         logger.error(f"❌ エラー発生: {e}")

# 会話履歴を基にプロンプトを生成する関数
def generate_prompt_with_history(drug_name: str, info_type: str, pmda_url: str, user_id: str) -> str:

    pre_conversation_history = get_user_conversation_history(user_id)

    # 会話履歴を文字列に変換
    if not pre_conversation_history:
        conversation_history = "過去の会話履歴はありません。"
    else:
        conversation_history = '\n'.join(
            f"ユーザー: {conv.user_message}\nボット: {conv.bot_response}" for conv in pre_conversation_history
        )


    return (f"ユーザーとの過去の会話:\n{conversation_history}\n"
            f"薬剤名: {drug_name}\n"
            f"知りたい情報: {info_type}\n"
            f"以下のPMDAのURLから得られる情報を参考にして、薬についてユーザーにわかりやすい説明をしてください。\n"
            f"URL: {pmda_url}")


# 指定したプロンプトを基に、OpenAI GPTからのレスポンスを非同期に取得する関数
def generate_natural_language_response(prompt: str, model: str = "gpt-4") -> str:
    logger.info("Generating response based on the provided prompt.")
    client = OpenAI(api_key=api_key)
    response = client.chat.completions.create(
        model=model,
        messages=[
            {"role": "system", "content": "You are a helpful assistant."},
            {"role": "user", "content": prompt}
        ],
        max_tokens=500,  # 最大500トークンまでの応答
        temperature=0.5,  # 値が0に近いほど、モデルはより決定的な応答を生成
        top_p=1  # すべてのトークンを考慮する
    )
    return response.choices[0].message.content.strip()

# check_relevance: 応答が薬品に関連しているかどうかをチェックする
def check_relevance(response: str) -> str:
    logger.info(f"Checking relevance of response: {response}")
    if "薬" in response or "副作用" in response or "使い方" in response:
        return response
    else:
        logger.warning("Response is not relevant to the drug")
        return "薬品以外の質問には回答できません。"

# 薬剤に関する情報を取得する関数
def get_drug_info(drug_name: str, info_type: str, pmda_url: str, user_id:str, model: str = "gpt-4" ) -> str:
    # logger.info(f"◆ drug_info: {drug_name}")
    # logger.info(f"◆ info_type: {info_type}")
    # logger.info(f"◆ user_id: {user_id}")
    prompt = generate_prompt_with_history(drug_name, info_type, pmda_url , user_id)
    logger.info(f"◆ prompt: {prompt}")
    response = generate_natural_language_response(prompt, model)
    return response

# テストコード
def test_generate_prompt_with_history():
    drug_name = "アスピリン"
    info_type = "副作用"
    pmda_url = "https://www.pmda.go.jp/"
    user_id = "haruka_ku-min_meme"
    
    prompt = generate_prompt_with_history(drug_name, info_type, pmda_url, user_id)
    print(prompt)

if __name__ == "__main__":
    test_generate_prompt_with_history()
