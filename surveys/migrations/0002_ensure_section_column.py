from django.db import migrations, models


def ensure_section_column(apps, schema_editor):
    """
    Some databases may have been created before the section FK was introduced.
    Add the nullable section_id column if it is missing to prevent runtime errors.
    """
    connection = schema_editor.connection
    table_name = "surveys_surveyquestion"
    column_name = "section_id"

    with connection.cursor() as cursor:
        columns = [
            col.name
            for col in connection.introspection.get_table_description(cursor, table_name)
        ]

    if column_name in columns:
        return

    SurveyQuestion = apps.get_model("surveys", "SurveyQuestion")
    apps.get_model("surveys", "SurveySection")

    field = models.ForeignKey(
        "surveys.SurveySection",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="questions",
    )
    field.set_attributes_from_name("section")
    schema_editor.add_field(SurveyQuestion, field)


class Migration(migrations.Migration):

    dependencies = [
        ("surveys", "0001_initial"),
    ]

    operations = [
        # Reverse is intentionally a noop; the base schema already includes this
        # column, and dropping it would make earlier migration states invalid.
        migrations.RunPython(ensure_section_column, migrations.RunPython.noop),
    ]
