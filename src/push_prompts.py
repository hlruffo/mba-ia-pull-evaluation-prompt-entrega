"""
Script para fazer push de prompts otimizados ao LangSmith Prompt Hub.

Este script:
1. Lê os prompts otimizados de prompts/bug_to_user_story_v2.yml
2. Valida os prompts
3. Faz push PÚBLICO para o LangSmith Hub
4. Adiciona metadados (tags, descrição, técnicas utilizadas)

DICAS DE IMPLEMENTAÇÃO:

- O push é feito pelo cliente do LangSmith:

      from langsmith import Client
      from langchain_core.prompts import ChatPromptTemplate

      client = Client()
      prompt = ChatPromptTemplate.from_messages([
          ("system", system_prompt),
          ("user", user_prompt),
      ])
      url = client.push_prompt(
          f"{username}/bug_to_user_story_v2",
          object=prompt,
          is_public=True,
          description="...",
          tags=[...],
      )

- `username` vem de USERNAME_LANGSMITH_HUB no .env e precisa ser o seu handle
  do Hub. Se você ainda não tem um handle, veja as instruções no .env.example.

- A variável do template precisa ser {bug_report}, que é a chave de entrada
  usada no dataset de avaliação.

- Use `load_yaml` de utils.py para ler o arquivo .yml.
"""

import os
import sys
from pathlib import Path

from dotenv import load_dotenv
from langchain_core.prompts import ChatPromptTemplate
from langsmith import Client

from utils import check_env_vars, load_yaml, print_section_header


PROJECT_ROOT = Path(__file__).resolve().parent.parent
ENV_FILE = PROJECT_ROOT / ".env"
PROMPT_FILE = PROJECT_ROOT / "prompts" / "bug_to_user_story_v2.yml"

load_dotenv(ENV_FILE)


def validate_prompt(prompt_data: dict) -> tuple[bool, list]:
    """Valida o prompt otimizado antes do envio ao LangSmith."""
    errors = []

    for field in ("description", "system_prompt", "user_prompt", "version"):
        if not prompt_data.get(field):
            errors.append(f"Campo obrigatório ausente ou vazio: {field}")

    system_prompt = prompt_data.get("system_prompt", "")
    user_prompt = prompt_data.get("user_prompt", "")
    techniques = prompt_data.get("techniques_applied", [])

    if "{bug_report}" not in user_prompt:
        errors.append("user_prompt deve conter a variável {bug_report}")
    if "[TODO]" in system_prompt or "TODO" in system_prompt:
        errors.append("system_prompt ainda contém TODO")
    if not isinstance(techniques, list) or len(techniques) < 2:
        errors.append("O prompt deve listar pelo menos duas técnicas")
    if "Few-shot Learning" not in techniques:
        errors.append("Few-shot Learning é obrigatório")

    return not errors, errors


def push_prompt_to_langsmith(prompt_name: str, prompt_data: dict) -> bool:
    """Faz push público do prompt otimizado ao LangSmith Prompt Hub."""
    client = Client()
    prompt = ChatPromptTemplate.from_messages([
        ("system", prompt_data["system_prompt"]),
        ("human", prompt_data["user_prompt"]),
    ])

    url = client.push_prompt(
        prompt_name,
        object=prompt,
        is_public=True,
        description=prompt_data["description"],
        tags=prompt_data["techniques_applied"],
    )
    print(f"✅ Prompt publicado: {prompt_name}")
    print(f"🔗 URL retornada: {url}")
    return True


def main() -> int:
    """Valida o YAML e publica o prompt versionado."""
    print_section_header("PUSH DO PROMPT OTIMIZADO")

    if not check_env_vars(["LANGSMITH_API_KEY", "USERNAME_LANGSMITH_HUB"]):
        return 1

    prompt_data = load_yaml(str(PROMPT_FILE))
    if not prompt_data:
        return 1

    is_valid, errors = validate_prompt(prompt_data)
    if not is_valid:
        print("❌ Prompt inválido:")
        for error in errors:
            print(f"   - {error}")
        return 1

    username = os.environ["USERNAME_LANGSMITH_HUB"]
    prompt_name = f"{username}/bug_to_user_story_v2"

    try:
        push_prompt_to_langsmith(prompt_name, prompt_data)
    except Exception as exc:
        print(f"❌ Falha ao publicar {prompt_name}: {exc}")
        return 1

    return 0


if __name__ == "__main__":
    sys.exit(main())
