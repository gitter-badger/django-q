# simple countdown, returns nothing
def countdown(n):
    while n > 0:
        n -= 1


def multiply(x, y):
    return x * y


def count_letters(tup):
    total = 0
    for word in tup:
        total += len(word)
    return total


def count_letters2(obj):
    return count_letters(obj.get_words())


def word_multiply(x, word=''):
    return len(word) * x


def get_task_name(task):
    return task.name


def result(obj):
    print('RESULT HOOK {} : {}'.format(obj.name, obj.result))
