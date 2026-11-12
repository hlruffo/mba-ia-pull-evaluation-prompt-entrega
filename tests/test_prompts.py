"""
Testes automatizados para validação de prompts.
"""
import pytest
import yaml
import sys
from pathlib import Path

# Adicionar src ao path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from utils import validate_prompt_structure

def load_prompts(file_path: str):
    """Carrega prompts do arquivo YAML."""
    with open(file_path, 'r', encoding='utf-8') as f:
        return yaml.safe_load(f)

class TestPrompts:
    @staticmethod
    def _prompt_data():
        prompt_path = Path(__file__).parent.parent / "prompts" / "bug_to_user_story_v2.yml"
        data = load_prompts(str(prompt_path))
        assert data is not None, f"Não foi possível carregar {prompt_path}"
        return data

    def test_prompt_has_system_prompt(self):
        """Verifica se o campo 'system_prompt' existe e não está vazio."""
        data = self._prompt_data()
        assert isinstance(data.get("system_prompt"), str)
        assert data["system_prompt"].strip()

    def test_prompt_has_role_definition(self):
        """Verifica se o prompt define uma persona."""
        data = self._prompt_data()
        system_prompt = data["system_prompt"]
        assert "Você é" in system_prompt
        assert "Product Manager" in system_prompt

    def test_prompt_mentions_format(self):
        """Verifica se o prompt exige formato Markdown ou User Story padrão."""
        data = self._prompt_data()
        system_prompt = data["system_prompt"]
        assert "User Story" in system_prompt
        assert "Critérios de Aceitação" in system_prompt
        assert "Dado" in system_prompt
        assert "Quando" in system_prompt
        assert "Então" in system_prompt

    def test_prompt_has_few_shot_examples(self):
        """Verifica se o prompt contém exemplos de entrada/saída."""
        data = self._prompt_data()
        system_prompt = data["system_prompt"]
        assert "Few-shot" in system_prompt
        assert "Exemplo 1" in system_prompt
        assert "Exemplo 2" in system_prompt
        assert "Entrada:" in system_prompt
        assert "Saída:" in system_prompt

    def test_prompt_no_todos(self):
        """Garante que você não esqueceu nenhum `[TODO]` no texto."""
        data = self._prompt_data()
        serialized = yaml.safe_dump(data, allow_unicode=True)
        assert "[TODO]" not in serialized
        assert "TODO" not in serialized

    def test_minimum_techniques(self):
        """Verifica se pelo menos 2 técnicas foram listadas nos metadados."""
        data = self._prompt_data()
        techniques = data.get("techniques_applied")
        assert isinstance(techniques, list)
        assert len(techniques) >= 2
        assert "Few-shot Learning" in techniques


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])