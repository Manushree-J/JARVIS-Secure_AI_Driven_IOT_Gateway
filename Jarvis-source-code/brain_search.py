from brain import get_notes

brain = get_notes()

while True:

    question = input("\nQuestion: ")

    if question.lower() == "exit":
        break

    question = question.lower()

    found = False

    for line in brain.split("\n"):

        if question in line.lower():

            print("\nFound:")
            print(line)

            found = True

    if not found:
        print("\nNothing found.")