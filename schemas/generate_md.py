from json_schema_for_humans.generate import generate_from_filename, generate_from_schema
from json_schema_for_humans.generation_configuration import GenerationConfiguration

config = GenerationConfiguration(copy_css=False, expand_buttons=True, template_name='md')

generate_from_filename(r"C:\Users\plopez\btap_batch\schemas\analysis_config_schema.yml", "schema_doc.html", config=config)

# Your doc is now in a file named "schema_doc.html". Next to it, "schema_doc.min.js" was copied, but not "schema_doc.css"
# Your doc will contain a "Expand all" and a "Collapse all" button at the top