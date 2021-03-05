import nltk



def get_after_prefix(paragraph, phrases):
    post = set()
    for p in phrases:
        #p = nltk.word_tokenize(phrase)
        for i in range(len(paragraph)):
            if p[0] == paragraph[i]:
                match = True
                L = len(p)
                if i+L < len(paragraph):
                    for k in range(1,L):
                        w1 = p[k]
                        w2 = paragraph[i+k]
                        if p[k] != paragraph[i+k]:
                            match = False
                            break
                    if match:
                        post.add(paragraph[i+L])
    return post


def apply(func, array):
    A = []
    for a in array:
        A.append(func(a))
    return A

para = 'using an oven, cook the chicken'
p = ["using an ", "cook a", "the chicken","chicken is yiummy"]
p = apply(nltk.word_tokenize,p)
para = nltk.word_tokenize(para)
print(get_after_prefix(para, p))