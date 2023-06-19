def convert(text):
    text = text.replace(":)", "🙂")
    text = text.replace(":(", "🙁")
    return text


def main():
    answer = input("")
    converted_text = convert(answer)
    print(converted_text)


main()
