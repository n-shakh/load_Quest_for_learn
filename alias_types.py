from typing import TypeAlias
from selenium import webdriver

TextQuestion: TypeAlias = str
URLPicture: TypeAlias = str
IdAnswer: TypeAlias = str
TextAnswer: TypeAlias = str
ChoiceAnswer: TypeAlias = list[dict[IdAnswer, TextAnswer]]
Answer: TypeAlias = int
Check: TypeAlias = bool
DictQuestion: TypeAlias = dict[TextQuestion, URLPicture, ChoiceAnswer, Answer, Check]


TextBlockQuestion: TypeAlias = str

Chrome: TypeAlias = webdriver.Chrome
PathJsonFile: TypeAlias = str
DictJsonFile: TypeAlias = dict

DictIdJsonFile: TypeAlias = dict[IdChapter, int]

PathBufQuestionFile: TypeAlias = str
BufQuestion: TypeAlias = dict[TextQuestion, URLPicture, int]

IdChapter: TypeAlias = str

