from django.db import models


class ResponseType(models.Model):
    """
    Defines a type of response, e.g., 'Single Choice', 'Free Text'.
    """
    name = models.CharField(
        max_length=100,
        unique=True,
        help_text="The type of response (e.g., Single Choice, Numeric)."
    )

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = "Response Type"
        verbose_name_plural = "Response Types"


class Response(models.Model):
    """
    Represents a single predefined answer/choice.
    """
    text_ar = models.CharField(max_length=255, verbose_name="Text in Arabic")
    text_en = models.CharField(max_length=255, verbose_name="Text in English")

    def __str__(self):
        return f"{self.text_en} / {self.text_ar}"

    class Meta:
        verbose_name = "Response"
        verbose_name_plural = "Responses"


class SurveyQuestion(models.Model):
    """
    A single question in a survey.
    """
    text_ar = models.TextField(verbose_name="Text in Arabic")
    text_en = models.TextField(verbose_name="Text in English")
    response_type = models.ForeignKey(
        ResponseType,
        on_delete=models.PROTECT,  # Prevent deleting a type that is in use
        related_name="questions",
    )
    possible_responses = models.ManyToManyField(
        Response,
        blank=True,  # Not all questions have predefined responses (e.g., free text)
        related_name="questions",
        help_text="Select possible responses for choice-based questions."
    )

    def __str__(self):
        return self.text_en

    class Meta:
        verbose_name = "Survey Question"
        verbose_name_plural = "Survey Questions"
