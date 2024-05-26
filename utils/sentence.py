import logging

import regex as re

from utils.data_utils import check_is_none
from utils.classify_language import classify_language, split_alpha_nonalpha


def _expand_abbreviations(text):
    pattern = r'(?<=[a-z])(?=[A-Z])|(?<=[A-Z])(?=[A-Z])'
    return re.sub(pattern, ' ', text)


def _expand_hyphens(text):
    pattern = r'(?<=[a-zA-Z])-(?=[a-zA-Z])'
    expanded_text = re.sub(pattern, ' ', text)
    return expanded_text


def markup_language(text: str, target_languages: list = None) -> str:
    pattern = r'[\!\"\#\$\%\&\'\(\)\*\+\,\-\.\/\:\;\<\>\=\?\@\[\]\{\}\\\\\^\_\`' \
              r'\！？。＂＃＄％＆＇（）＊＋，－／：；＜＝＞＠［＼］＾＿｀｛｜｝～｟｠｢｣､、〃》「」' \
              r'『』【】〔〕〖〗〘〙〚〛〜〝〞〟〰〾〿–—‘\'\‛\“\”\„\‟…‧﹏.]+'
    sentences = re.split(pattern, text)

    pre_lang = ""
    p = 0

    new_sentences = []
    for sentence in sentences:
        new_sentences.extend(split_alpha_nonalpha(sentence))
    sentences = new_sentences

    for sentence in sentences:
        if check_is_none(sentence): continue

        lang = classify_language(sentence, target_languages)

        if pre_lang == "":
            text = text[:p] + text[p:].replace(sentence, f"[{lang.upper()}]{sentence}", 1)
            p += len(f"[{lang.upper()}]")
        elif pre_lang != lang:
            text = text[:p] + text[p:].replace(sentence, f"[{pre_lang.upper()}][{lang.upper()}]{sentence}", 1)
            p += len(f"[{pre_lang.upper()}][{lang.upper()}]")
        pre_lang = lang
        p += text[p:].index(sentence) + len(sentence)
    text += f"[{pre_lang.upper()}]"

    return text


def split_languages(text: str, target_languages: list = None, segment_size: int = 50,
                    expand_abbreviations: bool = False, expand_hyphens: bool = False) -> list:
    pattern = r'[\!\"\#\$\%\&\'\(\)\*\+\,\-\.\/\:\;\<\>\=\?\@\[\]\{\}\\\\\^\_\`' \
              r'\！？\。＂＃＄％＆＇（）＊＋，－／：；＜＝＞＠［＼］＾＿｀｛｜｝～｟｠｢｣､、〃》「」' \
              r'『』【】〔〕〖〗〘〙〚〛〜〝〞〟〰〾〿–—‘\'\‛\“\”\„\‟…‧﹏.]+'
    sentences = re.split(pattern, text)

    pre_lang = ""
    start = 0
    end = 0
    sentences_list = []

    new_sentences = []
    for sentence in sentences:
        new_sentences.extend(split_alpha_nonalpha(sentence))
    sentences = new_sentences

    for sentence in sentences:
        if check_is_none(sentence):
            continue

        lang = classify_language(sentence, target_languages)

        end += text[end:].index(sentence)
        if pre_lang != "" and pre_lang != lang:
            _text = text[start:end]
            if pre_lang == "en":
                if expand_abbreviations:
                    _text = _expand_abbreviations(_text)
                if _expand_hyphens:
                    _text = _expand_hyphens(_text)

            if len(_text) >= segment_size:
                for i in sentence_split(_text, segment_size):
                    sentences_list.append((i, pre_lang))
            else:
                sentences_list.append((_text, pre_lang))
            start = end
        end += len(sentence)
        pre_lang = lang

    _text = text[start:]
    if pre_lang == "en":
        if expand_abbreviations:
            _text = _expand_abbreviations(_text)
        if _expand_hyphens:
            _text = _expand_hyphens(_text)
    if len(_text) >= segment_size:
        for i in sentence_split(_text, segment_size):
            sentences_list.append((i, pre_lang))
    else:
        sentences_list.append((_text, pre_lang))

    return sentences_list


def sentence_split(text: str, segment_size: int) -> list:
    # Split text into paragraphs
    paragraphs = re.split(r'\r\n|\n', text)
    pattern = r'[!(),—+\-.:;?？。，、；：]+'
    sentences_list = []

    for paragraph in paragraphs:
        sentences = re.split(pattern, paragraph)
        discarded_chars = re.findall(pattern, paragraph)

        count, p = 0, 0

        # Iterate over the symbols by which it is split
        for i, discarded_char in enumerate(discarded_chars):
            count += len(sentences[i]) + len(discarded_char)
            if count >= segment_size:
                sentences_list.append(paragraph[p:p + count].strip())
                p += count
                count = 0

        # Add the remaining text
        if len(paragraph) - p > 0:
            if len(paragraph) - p <= 4 and len(sentences_list) > 0:
                sentences_list[-1] += paragraph[p:]
            else:
                sentences_list.append(paragraph[p:])

    # Uncomment the following lines if you want to log the sentences
    # for sentence in sentences_list:
    #     logging.debug(sentence)

    return sentences_list


def sentence_split_reading(text: str) -> list:
    pattern = r'“[^“”]*”|[^“”]+'
    parts = re.findall(pattern, text)

    sentences_list = []
    for part in parts:
        if part:
            is_quote = part.startswith("“") and part.endswith("”") and part[-2] in "！！？。，；……?!.,;"

            if is_quote:
                sentence = part.strip("“”")
                sentences_list.append((sentence, is_quote))
            else:
                if len(sentences_list) > 0 and not sentences_list[-1][1]:
                    sentences_list[-1] = (sentences_list[-1][0] + part, sentences_list[-1][1])
                else:
                    sentences_list.append((part, is_quote))

    return sentences_list


def sentence_split_and_markup(text, segment_size=50, lang="auto", speaker_lang=None):
    # 如果该speaker只支持一种语言
    if speaker_lang is not None and len(speaker_lang) == 1:
        if lang.upper() not in ["AUTO", "MIX"] and lang.lower() != speaker_lang[0]:
            logging.debug(
                f"lang \"{lang}\" is not in speaker_lang {speaker_lang},automatically set lang={speaker_lang[0]}")
        lang = speaker_lang[0]

    sentences_list = []
    if lang.upper() != "MIX":
        if segment_size <= 0:
            sentences_list.append(
                markup_language(text,
                                speaker_lang) if lang.upper() == "AUTO" else f"[{lang.upper()}]{text}[{lang.upper()}]")
        else:
            for i in sentence_split(text, segment_size):
                if check_is_none(i): continue
                sentences_list.append(
                    markup_language(i,
                                    speaker_lang) if lang.upper() == "AUTO" else f"[{lang.upper()}]{i}[{lang.upper()}]")
    else:
        sentences_list.append(text)

    for i in sentences_list:
        logging.debug(i)

    return sentences_list


if __name__ == '__main__':
    text = """这几天心里颇不宁静。
    今晚在院子里坐着乘凉，忽然想起日日走过的荷塘，在这满月的光里，总该另有一番样子吧。月亮渐渐地升高了，墙外马路上孩子们的欢笑，已经听不见了；妻在屋里拍着闰儿，迷迷糊糊地哼着眠歌。我悄悄地披了大衫，带上门出去。"""
    # print(markup_language(text, target_languages=None))
    print(sentence_split(text, segment_size=50))
    # print(sentence_split_and_markup(text, segment_size=50, lang="auto", speaker_lang=None))
    # text = "你好hello，这是一段用来测试vits自动标注的文本。こんにちは,これは自動ラベリングのテスト用テキストです.Hello, this is a piece of text to test autotagging."
    # print(split_languages(text, ["zh", "ja", "en"]))
