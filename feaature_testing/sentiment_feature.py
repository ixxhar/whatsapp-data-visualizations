import pandas as pd
import re
import string
import regex
import emoji

from nltk import word_tokenize, pos_tag

from textblob import TextBlob

# Let's create a function to pull out nouns from a string of text
def nouns_adj(text):
    '''Given a string of text, tokenize the text and pull out only the nouns and adjectives.'''
    is_noun_adj = lambda pos: pos[:2] == 'NN' or pos[:2] == 'JJ'
    tokenized = word_tokenize(text)
    nouns_adj = [word for (word, pos) in pos_tag(tokenized) if is_noun_adj(pos)]
    return ' '.join(nouns_adj)


def clean_text(text):
    '''
    1. lower case
    2. new line remove
    3. url remove
    4. punctuations, quotations, other unnecessary things removed
    '''
    text = text.lower()
    text = re.sub('\n', '', text)
    text = re.sub("https?://\S+", "", text)
    text = re.sub('\[.*?\]', '', text)
    text = re.sub('[%s]' % re.escape(string.punctuation), '', text)
    text = re.sub('\w*\d\w*', '', text)
    text = re.sub('[‘’“”…]', '', text)
    re.sub('\r?\n', '', text)
    return text


def clean_media_voice_video_emojis(text):
    if ('Missed voice call') in text:
        text = None
        return text
    elif ('Missed video call') in text:
        text = None
        return text
    elif ('<Media omitted>') in text:
        text = None
        return text
    else:
        processed_text = []
        data = regex.findall(r'\X', text)
        for word in data:
            if not any(char in emoji.UNICODE_EMOJI for char in word):
                processed_text.append(word)

        return clean_text("".join(processed_text))


if __name__ == '__main__':
    pd.set_option('max_colwidth', 50)
    pd.set_option('display.max_columns', None)

    whatsapp_chat_file = open('../../data/chat_muaz_small.txt', 'r')
    df = pd.DataFrame(data=[line.split(' - ', 1) for line in whatsapp_chat_file], columns=['DateTime', 'Message'])
    df[['Member', 'Message']] = df.Message.apply(lambda x: pd.Series(str(x).split(":", 1)))

    df = df.dropna()

    df['DateTime'] = pd.to_datetime(df['DateTime'])

    df['CleanMessage'] = pd.DataFrame(df.Message.apply(lambda x: clean_media_voice_video_emojis(x))).dropna()

    df_clean = df[['DateTime', 'Member', "Message", 'CleanMessage']].dropna()

    # print(df_clean)

    pol = lambda x: TextBlob(x).sentiment.polarity
    sub = lambda x: TextBlob(x).sentiment.subjectivity

    df_clean['polarity'] = df_clean['CleanMessage'].apply(pol)  # -1: Negative, +1: Positive
    df_clean['subjectivity'] = df_clean['CleanMessage'].apply(sub)  # 0: Objective (fact), 1: Subject (opinion)

    print(df_clean.query('polarity<0')[['DateTime', 'Member', 'Message', 'polarity']].sort_values(by=['DateTime'],ascending=False)[0:10])