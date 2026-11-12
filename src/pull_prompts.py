"""
Script para fazer pull de prompts do LangSmith Prompt Hub.

Este script:
1. Conecta ao LangSmith usando credenciais do .env
2. Faz pull do prompt semente do desafio
3. Salva localmente em prompts/bug_to_user_story_v1.yml

DICAS DE IMPLEMENTAÇÃO:

- O pull é feito pelo cliente do LangSmith:

      from langsmith import Client
      client = Client()
      prompt = client.pull_prompt(
          "leonanluppi/bug_to_user_story_v1",
          dangerously_pull_public_prompt=True,
      )

- O parâmetro `dangerously_pull_public_prompt=True` é obrigatório sempre que o
  identificador tem dono explícito ("owner/nome"). O LangSmith bloqueia esse pull
  por padrão porque um prompt do Hub é um objeto LangChain serializado, que pode
  vir de terceiros. Aqui o prompt é o do desafio, então o risco é conhecido.

- O retorno é um ChatPromptTemplate. Para extrair o conteúdo das mensagens,
  use a serialização nativa do LangChain (`prompt.messages`, e o atributo
  `.prompt.template` de cada mensagem).

- Use `save_yaml` de utils.py para gravar o resultado no arquivo .yml.
"""

import os
import sys
from pathlib import Path

from dotenv import load_dotenv
from langsmith import Client

from utils import check_env_vars, print_section_header, save_yaml


PROJECT_ROOT = Path(__file__).resolve().parent.parent
ENV_FILE = PROJECT_ROOT / ".env"
OUTPUT_FILE = PROJECT_ROOT / "prompts" / "bug_to_user_story_v1.yml"
PROMPT_NAME = "leonanluppi/bug_to_user_story_v1"

load_dotenv(ENV_FILE)


def _message_role(message) -> str:
    """Converte a classe de mensagem LangChain em um papel estável."""
    message_type = getattr(message, "type", None)
    if message_type in {"system", "human", "user", "ai", "tool"}:
        return "user" if message_type == "human" else message_type

    class_name = message.__class__.__name__.lower()
    if "system" in class_name:
        return "system"
    if "human" in class_name:
        return "user"
    if "ai" in class_name:
        return "assistant"
    if "tool" in class_name:
        return "tool"
    return "unknown"


def _message_content(message) -> str:
    """Extrai o template textual de uma mensagem LangChain."""
    prompt_template = getattr(message, "prompt", None)
    if prompt_template is not None and hasattr(prompt_template, "template"):
        return prompt_template.template

    content = getattr(message, "content", "")
    return content if isinstance(content, str) else str(content)


def pull_prompts_from_langsmith() -> dict:
    """Baixa o prompt público inicial e converte-o para o YAML do projeto."""
    client = Client()
    prompt = client.pull_prompt(
        PROMPT_NAME,
        dangerously_pull_public_prompt=True,
    )

    messages = []
    for message in getattr(prompt, "messages", []):
        role = _message_role(message)
        messages.append({"role": role, "content": _message_content(message)})

    system_parts = [item["content"] for item in messages if item["role"] == "system"]
    user_parts = [
        item["content"]
        for item in messages
        if item["role"] in {"human", "user"}
    ]

    prompt_data = {
        "description": "Prompt semente obtido do LangSmith Prompt Hub.",
        "source": PROMPT_NAME,
        "version": "v1",
        "system_prompt": "\\n\\n".join(system_parts),
        "user_prompt": "\\n\\n".join(user_parts),
        "messages": messages,
    }

    if not save_yaml(prompt_data, OUTPUT_FILE):
        raise RuntimeError(f"Não foi possível salvar {OUTPUT_FILE}")

    return prompt_data


def main() -> int:
    """Valida o ambiente, executa o pull e informa o arquivo gerado."""
    print_section_header("PULL DO PROMPT INICIAL")

    if not check_env_vars(["LANGSMITH_API_KEY"]):
        return 1

    try:
        prompt_data = pull_prompts_from_langsmith()
    except Exception as exc:
        print(f"❌ Falha ao fazer pull de {PROMPT_NAME}: {exc}")
        return 1

    print(f"✅ Prompt obtido: {PROMPT_NAME}")
    print(f"✅ Mensagens extraídas: {len(prompt_data['messages'])}")
    print(f"✅ Arquivo salvo: {OUTPUT_FILE}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
