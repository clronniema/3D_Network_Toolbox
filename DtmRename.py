import os
import sys

def replace_vowel(original_word):
    vowels = "aeiou "
    new_word = ""
    # Replacing each of the vowels and space to lowercase and nothing
    for letter in original_word:
        if letter not in vowels:
            new_word += (letter.lower())
    return new_word


def main(dir_path):
    if os.path.isdir(dir_path):
        print("Directory '{0}' exists, renaming now.".format(dir_path))
        os.chdir(dir_path)
        for src in os.listdir():
            # if path is not a directory or folder
            if not os.path.isdir(src):
                arr_filename = src.split(".")
                new_filename = "{0}.{1}".format(replace_vowel(arr_filename[0]), arr_filename[1])
                os.rename(src, new_filename)
                print("Renamed '{0}' to '{1}'".format(src, new_filename))
            else:
                print("'{0}' is a folder, cannot be renamed".format(src))
    else:
        print("Directory '{0}' does not exist, ending script.".format(dir_path))

if __name__ == "__main__":
    print("==== Renaming Script begins ====")
    # Execute through this only if run as standalone script
    main(sys.argv[1])
    print("==== Renaming Script ends ====")
