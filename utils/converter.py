def float_to_dec(val_str, base):
    if '.' not in val_str: return int(val_str, base)
    whole, frac = val_str.split('.')
    dec_val = int(whole, base) if whole else 0
    for i, digit in enumerate(frac):
        # Hexadecimal support for fractional part
        if digit.upper() in 'ABCDEF': val = ord(digit.upper()) - 55
        else: val = int(digit)
        dec_val += val * (base ** -(i + 1))
    return dec_val

def dec_to_base_float(n, base, precision=5):
    whole = int(n)
    frac = n - whole
    
    if base == 2: res_whole = bin(whole)[2:]
    elif base == 8: res_whole = oct(whole)[2:]
    elif base == 16: res_whole = hex(whole)[2:].upper()
    else: return str(n)

    if frac == 0: return res_whole
    
    res_frac = "."
    while frac > 0 and len(res_frac) <= precision + 1:
        frac *= base
        digit = int(frac)
        if base == 16: res_frac += hex(digit)[2:].upper()
        else: res_frac += str(digit)
        frac -= digit
    return res_whole + res_frac

def dec_to_gray(n): return bin(n ^ (n >> 1))[2:]
def dec_to_excess3(n): return "".join([f"{(int(d) + 3):04b}" for d in str(n) if d.isdigit()])

def get_explanation(value_str, from_base, decimal_val, is_float):
    exp = "\n\n💡 **কনভার্শন ব্যাখ্যা (Step-by-Step Explanation):**\n"
    if from_base != "dec":
        exp += f"১. প্রথমে {from_base.upper()} ভ্যালু `{value_str}` কে ডেসিমেল (Decimal) এ রূপান্তর করা হয়েছে।\n"
    
    exp += f"২. ডেসিমেল মান `{decimal_val}` কে বাইনারিতে নিতে ২ দিয়ে, অক্টালে নিতে ৮ দিয়ে এবং হেক্সাডেসিমেলে নিতে ১৬ দিয়ে ভাগ করা হয়েছে (পূর্ণসংখ্যার ক্ষেত্রে ভাগশেষ নেওয়া হয়েছে)।\n"
    
    if is_float:
        exp += "৩. দশমিকের (Fraction) পরের অংশের জন্য উক্ত বেজ (২, ৮ বা ১৬) দিয়ে বারবার গুণ করে পূর্ণসংখ্যাগুলোকে নেওয়া হয়েছে।\n"
        
    exp += "৪. **Gray Code:** বাইনারি মানের সাথে তার 1-bit Right-shifted মানের XOR (^) অপারেশন করে গ্রে কোড বের করা হয়েছে।\n"
    exp += "৫. **Excess-3 Code:** ডেসিমেল সংখ্যার প্রতিটি ডিজিটের সাথে আলাদাভাবে ৩ যোগ করে তার ৪-বিটের বাইনারি মান পাশাপাশি বসানো হয়েছে।"
    return exp

def convert_all(value_str, from_base):
    try:
        base_map = {"dec": 10, "bin": 2, "oct": 8, "hex": 16}
        if from_base not in base_map: return "❌ Error: Unsupported base."
        
        b = base_map[from_base]
        decimal_val = float_to_dec(value_str, b)
        
        if decimal_val < 0: return "❌ Error: Negative values not supported."

        is_float = '.' in value_str
        
        if is_float:
            res_bin = dec_to_base_float(decimal_val, 2)
            res_oct = dec_to_base_float(decimal_val, 8)
            res_hex = dec_to_base_float(decimal_val, 16)
            res_gray = "N/A (Integers Only)"
            res_e3 = "N/A (Integers Only)"
        else:
            decimal_val = int(decimal_val)
            res_bin = bin(decimal_val)[2:]
            res_oct = oct(decimal_val)[2:]
            res_hex = hex(decimal_val)[2:].upper()
            res_gray = dec_to_gray(decimal_val)
            res_e3 = dec_to_excess3(decimal_val)

        explanation = get_explanation(value_str, from_base, decimal_val, is_float)

        return (
            f"🔢 **Advanced Conversion Results**\n"
            f"Input: `{value_str}` ({from_base.upper()})\n\n"
            f"🔹 **Decimal:** `{decimal_val}`\n"
            f"🔹 **Binary:** `{res_bin}`\n"
            f"🔹 **Octal:** `{res_oct}`\n"
            f"🔹 **Hexadecimal:** `{res_hex}`\n"
            f"🔹 **Gray Code:** `{res_gray}`\n"
            f"🔹 **Excess-3:** `{res_e3}`"
            f"{explanation}"
        )
    except Exception as e:
        return f"❌ **Error:** Invalid format for {from_base.upper()}."
