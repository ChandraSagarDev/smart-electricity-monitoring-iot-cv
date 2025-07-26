from billing import ElectricityBillCalculator

def test_billing():
    # Initialize calculator with default settings
    calculator = ElectricityBillCalculator(
        is_single_phase=True,
        is_bpl=False,
        connected_load=2000
    )
    
    # Test different consumption levels
    test_units = [30, 45, 75, 125, 175, 225, 275, 325, 375, 450, 550]
    
    for units in test_units:
        bill = calculator.calculate_bill(units)
        print(f"\nTest with {units} units:")
        print(f"Fixed Charge: Rs.{bill['fixed_charge']}")
        print(f"Energy Charge: Rs.{bill['energy_charge']}")
        print(f"ToD Charge: Rs.{bill['tod_charge']}")
        print(f"Duty: Rs.{bill['duty']}")
        print(f"Subsidy: Rs.{bill['subsidy']}")
        print(f"Total Amount: Rs.{bill['final']}")

# Entry point for running the billing calculator test cases.
if __name__ == "__main__":
    test_billing()
