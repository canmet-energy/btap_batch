# Known Issues
* The daylight_controls measure is not costing correctly with 3.7.0. This feature has been disabled for now. Link to bug tracker is [here]()
* Peak Heating and cooling outputs do not work with mixed fuel systems [Issue Link](https://github.com/canmet-energy/btap_tasks/issues/410)
* SHW tanks costing may be inconsistent with smaller tanks. In some situations RSMeans costs smaller tanks as more 
expensive than larger ones, which may lead to awkward economics when using the  [Issues Link](https://github.com/canmet-energy/btap_tasks/issues/417)
* Currently costs of mitigating thermal bridging effects of constructions due to building geometry (corners, edges) are not accounted for. 
