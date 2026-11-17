import pytest
from pydantic import ValidationError

from app.domain.schemas import (
    AlternativeSchema,
    QuestionItemSchema,
    QuestionnaireOutput,
)


def test_giunti_pdf_example_validates_exact_schema() -> None:
    """
    Test function to validate the schema of a Giunti PDF questionnaire.
    This test checks that the payload for a Giunti questionnaire adheres to the expected schema.
    It verifies the following aspects:
    - The title, language, and total number of items in the questionnaire.
    - The structure and content of each item, including:
        - The item number and statement.
        - The type of question (Likert scale, multiple choice, or open-ended).
        - The alternatives provided for multiple choice questions.
        - The correct answer for each question, ensuring it matches the expected format.
    Assertions are made to confirm:
    - The correct values for title, language, and total items.
    - The data types of values in alternatives for different question types.
    - The correctness of the specified correct answers.
    """
    
    payload = {
        "titulo": "Questionario di esempio",
        "idioma": "it",
        "total_items": 3,
        "items": [
            {
                "numero": 1,
                "enunciado": "Mi preoccupo eccessivamente per cose di poca importanza.",
                "tipo": "escala_likert",
                "alternativas": [
                    {"valor": 0, "texto": "Mai"},
                    {"valor": 1, "texto": "A volte"},
                    {"valor": 2, "texto": "Spesso"},
                    {"valor": 3, "texto": "Sempre"},
                ],
                "respuesta_correcta": None,
            },
            {
                "numero": 2,
                "enunciado": "Quale numero completa la serie: 2, 4, 8, 16, ...?",
                "tipo": "seleccion_multiple",
                "alternativas": [
                    {"valor": "A", "texto": "18"},
                    {"valor": "B", "texto": "24"},
                    {"valor": "C", "texto": "32"},
                ],
                "respuesta_correcta": "C",
            },
            {
                "numero": 3,
                "enunciado": "Descriva una situazione recente in cui si è sentito sotto pressione.",
                "tipo": "desarrollo",
                "alternativas": [],
                "respuesta_correcta": None,
            },
        ],
    }

    output = QuestionnaireOutput.model_validate(payload)

    assert output.titulo == "Questionario di esempio"
    assert output.idioma == "it"
    assert output.total_items == 3
    assert len(output.items) == 3

    # Verificar que en escala_likert el valor es int (0) y en seleccion_multiple es str ("A")
    assert output.items[0].alternativas[0].valor == 0
    assert isinstance(output.items[0].alternativas[0].valor, int)
    assert output.items[1].alternativas[0].valor == "A"
    assert isinstance(output.items[1].alternativas[0].valor, str)
    assert output.items[1].respuesta_correcta == "C"
    assert output.items[2].alternativas == []
    assert output.items[2].respuesta_correcta is None


@pytest.mark.parametrize(
    "item_type",
    [
        "escala_likert",
        "seleccion_multiple",
        "verdadero_falso",
        "desarrollo",
        "emparejamiento",
    ],
)
def test_all_five_item_types_are_supported(item_type: str) -> None:
    """Verifica que el esquema acepte los 5 tipos requeridos por Giunti."""
    item = QuestionItemSchema(
        numero=1,
        enunciado="Pregunta de prueba",
        tipo=item_type,  # type: ignore[arg-type]
        alternativas=[AlternativeSchema(valor="A", texto="Opción A")],
    )
    assert item.tipo == item_type


def test_invalid_item_type_raises_validation_error() -> None:
    """Verifica que un tipo de ítem no permitido lance ValidationError."""
    with pytest.raises(ValidationError):
        QuestionItemSchema(
            numero=1,
            enunciado="Pregunta inválida",
            tipo="pregunta_inventada",  # type: ignore[arg-type]
            alternativas=[],
        )


def test_likert_string_numbers_are_coerced_to_int() -> None:
    """Verifica que en escala_likert los valores numéricos en string ('0', '1') pasen a int."""
    item = QuestionItemSchema(
        numero=1,
        enunciado="Me siento tranquilo.",
        tipo="escala_likert",
        alternativas=[
            AlternativeSchema(valor="0", texto="Nunca"),
            AlternativeSchema(valor="1", texto="A veces"),
        ],
    )

    assert item.alternativas[0].valor == 0
    assert isinstance(item.alternativas[0].valor, int)
    assert item.alternativas[1].valor == 1
    assert isinstance(item.alternativas[1].valor, int)


def test_desarrollo_clears_alternatives_and_correct_answer() -> None:
    """Verifica que un ítem de desarrollo limpie alternativas y respuesta_correcta residuales."""
    item = QuestionItemSchema(
        numero=1,
        enunciado="Explique su respuesta.",
        tipo="desarrollo",
        alternativas=[AlternativeSchema(valor="A", texto="No debería estar")],
        respuesta_correcta="A",
    )

    assert item.alternativas == []
    assert item.respuesta_correcta is None


def test_total_items_is_auto_calculated_and_empty_items_rejected() -> None:
    """Verifica que total_items se recalcule siempre según len(items) y rechace listas vacías."""
    output = QuestionnaireOutput(
        titulo="Test Auto Conteo",
        idioma="  ES ",
        total_items=99,
        items=[
            QuestionItemSchema(
                numero=1,
                enunciado="Ítem único",
                tipo="desarrollo",
            )
        ],
    )

    assert output.idioma == "es"
    assert output.total_items == 1

    with pytest.raises(ValidationError):
        QuestionnaireOutput(
            titulo="Cuestionario Vacío",
            idioma="es",
            total_items=0,
            items=[],
        )
