from json_schema_for_humans.generate import generate_from_filename, generate_from_schema
from json_schema_for_humans.generation_configuration import GenerationConfiguration

config = GenerationConfiguration(copy_css=False, expand_buttons=True, template_name='md', description_is_markdown=True, examples_as_yaml=True)
generate_from_filename(r"build_config_schema.yml", "../docs/build_config_schema.md", config=config)
generate_from_filename(r"analysis_config_schema.yml", "../docs/analysis_config_schema.md", config=config)

