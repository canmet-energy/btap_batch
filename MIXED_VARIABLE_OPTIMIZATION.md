# BTAP Mixed Variable Optimization Guide

Your optimization now supports both discrete and continuous parameters!

## How it Works

### 1. Automatic Variable Type Detection
The system automatically detects whether each variable should be treated as continuous or discrete based on keywords in the variable name:

**Continuous Variables** (treated as floating-point):
- Variables containing: `scale`, `ratio`, `factor`, `efficiency`, `conductance`, `transmittance`, `shgc`, `u_value`, `r_value`

**Discrete Variables** (treated as categorical):
- All other variables (building types, HVAC systems, etc.)

### 2. Example Configuration

```yaml
building_options:
  :scale_factor: [0.5, 1.0, 1.5]           # → CONTINUOUS (contains "scale")
  :hvac_system: ["system1", "system2"]      # → DISCRETE
  :wall_conductance: [0.1, 0.2, 0.3]      # → CONTINUOUS (contains "conductance")
  :window_type: ["type1", "type2"]         # → DISCRETE
  :thermal_efficiency: [0.7, 0.8, 0.9]    # → CONTINUOUS (contains "efficiency")
  :building_type: ["office", "retail"]     # → DISCRETE
```

### 3. Algorithm Selection
The optimization automatically selects appropriate operators based on variable types:

- **Mixed Variables**: SBX crossover + Polynomial mutation (handles both types)
- **All Continuous**: SBX crossover + Polynomial mutation 
- **All Discrete**: Two-point crossover + Bit-flip mutation

### 4. Continuous Variable Processing
For continuous variables:
- Normalized to [0,1] range during optimization
- Automatically scaled to actual parameter ranges
- For numeric options: interpolates between min/max values
- For non-numeric options: treats as discrete (fallback)

## Benefits

✅ **No more sklearn LabelEncoder errors**
✅ **Proper floating-point optimization**
✅ **Automatic variable type detection**
✅ **Mixed discrete/continuous support**
✅ **Backward compatible with existing configurations**

## Manual Override

If you need to manually specify variable types, you can modify the `_detect_variable_types()` method in `BTAPOptimization` class to return your desired configuration.

## Example Usage

Your existing optimization configurations will work automatically. Just ensure your continuous parameters have appropriate keywords in their names, or they will be treated as discrete variables.

The system is now ready to handle both discrete categorical choices (like HVAC systems) and continuous numerical parameters (like efficiency factors) in the same optimization run!
