from typing import Literal, List, Self
from pydantic import BaseModel
from pydantic import model_validator, Field
from datetime import datetime

ItemType = Literal[
    "escala_likert",
    "seleccion_multiple",
    "verdadero_falso",
    "desarrollo",
    "emparejamiento",
]

JobStatus = Literal["QUEUED", "PROCESSING", "COMPLETED", "FAILED"]


class AlternativeSchema(BaseModel):
    """
    Schema representing an alternative option for a question item.
    Attributes:
        valor (str | int): The value of the alternative, which can be a string or
            an integer.
        texto (str): The text description of the alternative, must be at least 1 character long.
    """

    valor: int | str
    texto: str = Field(min_length=1)


class QuestionItemSchema(BaseModel):
    """
    QuestionItemScheme is a Pydantic model that represents a question item in a questionnaire.
    Attributes:
        numero (int): The question number, must be greater than or equal to 1.
        enunciado (str): The statement or text of the question, must have a minimum length of 1.
        tipo (ItemType): The type of the question, which determines its behavior and validation.
        alternativas (List[AlternativeSchema]): A list of alternative answers for the question,
          defaults to an empty list.
        respuesta_correcta (Union[int, str, None]): The correct answer for the question, can be an integer, string, or
        None.
    Validation:
        - After the model is created, the `validate_alternatives` method is called to enforce additional rules:
            - If the question type is "desarrollo", the alternatives are cleared and the correct answer is set to None.
            - If the question type is "escala_likert", it checks that each alternative's value can be converted to an
            integer.
    """

    numero: int = Field(ge=1)
    enunciado: str = Field(min_length=1)
    tipo: ItemType
    alternativas: List[AlternativeSchema] = Field(default_factory=list)
    respuesta_correcta: int | str | None = None

    @model_validator(mode="after")
    def validate_alternatives(self) -> Self:

        if self.tipo == "desarrollo":
            self.alternativas = []
            self.respuesta_correcta = None
        elif self.tipo == "escala_likert":
            for alt in self.alternativas:
                try:
                    alt.valor = int(alt.valor)
                except ValueError:
                    continue
        return self


class QuestionnaireOutput(BaseModel):
    """
    QuestionnaireOutput is a Pydantic model that represents the output structure of a questionnaire.
    Attributes:
        titulo (str): The title of the questionnaire. Must be at least 1 character long.
        idioma (str): The language of the questionnaire. Must be at least 2 characters long.
        total_items (int): The total number of items in the questionnaire. Defaults to 0 and must be non-negative.
        items (List[QuestionItemScheme]): A list of question items in the questionnaire. Must contain at least 1 item.
    Methods:
        validate_questionnaire: A model validator that strips whitespace from the 'idioma' attribute,
        converts it to lowercase, and updates 'total_items' based on the length of 'items'.
    """

    titulo: str = Field(min_length=1)
    idioma: str = Field(min_length=2)
    total_items: int = Field(default=0, ge=0)
    items: List[QuestionItemSchema] = Field(min_length=1)

    @model_validator(mode="after")
    def validate_questionnaire(self) -> Self:
        self.idioma = self.idioma.strip().lower()
        self.total_items = len(self.items)
        return self


class ExtractionJob(BaseModel):
    """
    ExtractionJob represents a job for extracting questionnaire data.
    Attributes:
        job_id (str): Unique identifier for the extraction job.
        filename (str): Name of the file associated with the extraction job.
        status (JobStatus): Current status of the job, default is "QUEUED".
        created_at (datetime): Timestamp when the job was created.
        completed_at (datetime | None): Timestamp when the job was completed, if applicable.
        result (QuestionnaireOutput | None): The output of the questionnaire extraction, if successful.
        error (str | None): Error message if the job failed, otherwise None.
    """

    job_id: str
    filename: str
    status: JobStatus = "QUEUED"
    created_at: datetime
    completed_at: datetime | None = None
    result: QuestionnaireOutput | None = None
    error: str | None = None
