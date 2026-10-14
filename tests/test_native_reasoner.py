from software.native_reasoner import solve


def test_arithmetic_is_solved_without_eval():
    assert solve("What is 17 * 19? Reply with the number only.") == "323"
    assert solve("What is 144 / 12? Reply with the number only.") == "12"
    assert solve("What is 256 + 789? Reply with the number only.") == "1045"
    assert solve("What is 1000 - 367? Reply with the number only.") == "633"


def test_basic_syllogism():
    assert solve("All zargs are blue. Nimo is a zarg. Is Nimo blue? Answer yes or no.") == "yes"


def test_ordered_comparison():
    prompt = "A is taller than B. B is taller than C. Who is shortest: A, B, or C? Reply with one letter."
    assert solve(prompt) == "C"


def test_weekday_arithmetic_with_words():
    prompt = "If today is Tuesday, what day is two days after tomorrow? Reply with the weekday."
    assert solve(prompt) == "Friday"


def test_exact_output_and_formatting():
    assert solve("Reply with exactly this token and nothing else: ARIES-OK") == "ARIES-OK"
    assert solve("Return exactly three items separated by commas: red, green, blue") == "red, green, blue"


def test_small_verified_fact():
    assert solve("At standard atmospheric pressure, what is the chemical formula for water? Reply with the formula only.") == "H2O"


def test_unknown_prompt_falls_back_to_model():
    assert solve("Write a poem about a blue mountain.") is None
