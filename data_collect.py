import re

#Get Expense/Salary Info
def income_collect():
    from calculate import banks
    banks_names =  ', '.join(sorted([info['Bank_Name'] for info in banks.values()]))

    #Amount regex
    amount_pattern = re.compile(r'^-?\d+(\.\d+)?$')
    #Date regex
    date_pattern = re.compile(r'^\d{4}-\d{2}-\d{2}$')
    #Necessity regex
    nec_pattern = re.compile(r'^(yes|no|y|n)$', re.IGNORECASE)

    #Get amount
    while True:
        try:
            amount_input = input("Enter amount (negative = expense, positive = salary): ").strip()
            if not amount_pattern.match(amount_input):
                raise ValueError("Invalid amount format!")
            
            amount = float(amount_input)
            if amount == 0:
                raise ValueError("Amount cannot be zero.")
            
            print("This is recorded as a SALARY." if amount > 0 else "This is recorded as an EXPENSE.")
            break
        except ValueError as e:
            print(e)

    #Bank name
    while True:
        name = input(f"Enter your bank name ({banks_names}): ").strip().lower()
        if not name:
            print("Bank name cannot be empty.")
            continue
        if name not in banks_names:
            print(f"Bank name can only be {banks_names}.")
            continue
        break

    #Get date
    while True:
        try:
            date_input = input("Enter date (YYYY-MM-DD): ").strip()
            if not date_pattern.match(date_input):
                raise ValueError("Invalid date format! Use YYYY-MM-DD.")
            
            year, month, day = map(int, date_input.split("-"))
            if not (1 <= month <= 12 and 1 <= day <= 31):
                raise ValueError("Invalid month/day in date!")
            break
        except ValueError as e:
            print(e)

    #Get necessity
    while True:
        try:
            nec_input = input("Is this a necessity? (yes/no): ").strip().lower()
            if not nec_pattern.match(nec_input):
                raise ValueError("Please answer 'yes' or 'no'.")
            nec = nec_input in ['yes', 'y']
            break
        except ValueError as e:
            print(e)

    return amount, name, date_input, nec


#Get Bank Info
def bank_collect():
    bank_pattern = re.compile(r'^[A-Za-z ]+$')
    number_pattern = re.compile(r'^\d+(\.\d+)?$')
    date_pattern = re.compile(r'^\d{4}-\d{2}-\d{2}$')

    #Bank name
    while True:
        bank_name = input("Enter your bank name: ").strip().lower()
        if not bank_name:
            print("Bank name cannot be empty.")
            continue
        if not bank_pattern.match(bank_name):
            print("Bank name can only contain letters and spaces.")
            continue
        break

    #Deposit amount
    while True:
        deposit_input = input("Enter the amount you put in the bank: ").strip()
        if not number_pattern.match(deposit_input):
            print("Invalid amount format! Please enter a number.")
            continue
        deposit = float(deposit_input)
        if deposit <= 0:
            print("Amount must be greater than zero.")
            continue
        break


    #Get date
    while True:
        try:
            date_input = input("Enter date (YYYY-MM-DD): ").strip()
            if not date_pattern.match(date_input):
                raise ValueError("Invalid date format! Use YYYY-MM-DD.")
            
            year, month, day = map(int, date_input.split("-"))
            if not (1 <= month <= 12 and 1 <= day <= 31):
                raise ValueError("Invalid month/day in date!")
            break
        except ValueError as e:
            print(e)

    #APR
    has_apr = input("Do you get an annual rate (APR)? (yes/no): ").strip().lower()
    if has_apr not in ["yes", "y"]:
        apr = None
        apr_type = None
        days = None
    else:
        while True:
            apr_input = input("Enter your APR percentage (e.g., 5 for 5%): ").strip()
            if not number_pattern.match(apr_input):
                print("Invalid APR format! Please enter a number.")
                continue
            apr = float(apr_input)
            if apr <= 0:
                print("APR must be greater than zero.")
                continue
            break

        while True:
            apr_type = input("Is it monthly or annually? (m/a): ").strip().lower()
            if apr_type in ["m", "monthly"]:
                apr_type = "Monthly"
                break
            elif apr_type in ["a", "annually"]:
                apr_type = "Annually"
                break
            else:
                print("Invalid input. Type 'm' for monthly or 'a' for annually.")

        #Number of days
        while True:
            days_input = input("Enter the number of days you'll keep the money in the bank: ").strip()
            if not number_pattern.match(days_input):
                print("Invalid format! Please enter a number.")
                continue
            days = int(float(days_input))
            if days <= 0:
                print("Days must be greater than zero.")
                continue
            break

    return bank_name, deposit, date_input, has_apr, apr, apr_type, days


#Function To Show And Combine Everything
#def main():
    print("\n--- Expense/Salary Section ---")
    finance_data = income_collect()
    
    print("\n--- Bank Section ---")
    bank_data = reserve_collect()

    combined = {
        "Finance Data": finance_data,
        "Bank Data": bank_data
    }

    print("\n✅ All data collected successfully:")
    print(combined)
    return combined

#Run everything
#if __name__ == "__main__":
    #main()