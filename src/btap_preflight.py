import copy
import logging
from .btap_parametric import BTAPParametric


# Class to manage preflight run with is to simply check if any custom OSM files can run.
class BTAPPreflight(BTAPParametric):
    def compute_scenarios(self):
        # Create default options scenario. Uses first value of all arrays.
        # precheck osm files for errors.
        osm_files = {}
        all_osm_files = self.get_local_osm_files()
        for filepath in all_osm_files:
            if filepath in self.engine.options[':building_type']:
                osm_files[filepath] = all_osm_files[filepath]
        # iterate through files.
        for osm_file in osm_files:
            run_option = copy.deepcopy(self.engine.options)
            # Set all options to nil/none.
            for key, value in self.engine.options.items():
                run_option[key] = None
            # lock weather location and other items.. this is simply to check if the osm files will run.
            run_option[':epw_file'] = 'CAN_QC_Montreal-Trudeau.Intl.AP.716270_CWEC2016.epw'
            run_option[':algorithm_type'] = self.engine.analysis_config[':algorithm'][':type']
            run_option[':template'] = 'NECB2011'
            run_option[':primary_heating_fuel'] = 'Electricity'
            # set osm file to pretest..if any.
            run_option[':building_type'] = osm_file
            # check basic items are in file.
            self.check_list(osm_files[osm_file])
            self.scenarios.append(run_option)

        message = f'Number of Scenarios {len(self.scenarios)}'
        logging.info(message)
        return self.scenarios
