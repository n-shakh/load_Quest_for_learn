import pandas as pd
from navig import read_json


def transfer_data():
    data = read_json()
    topics = {}
    for key in data:
        table = pd.json_normalize(data[key], max_level=1)

        list_answer = table.loc[:, 'answer']
        for answer in list_answer.items():
            list_answer[answer[0]] = f'Вариант {answer[1]}'
        dict_quest = {'text': 'Текст вопроса', 'picture': 'Картинка', 'answer': 'Ответ', 'check': 'Проверка'}
        dict_quest.update({f'choice.{i}': f'Вариант {i}' for i in range(1, 7)})
        table.rename(columns=dict_quest, inplace=True)
        topics[key] = table

    writer = pd.ExcelWriter('./output.xlsx', engine='xlsxwriter')
    workbook = writer.book
    wrap_format = workbook.add_format({'text_wrap': True})
    for sheet_name in topics.keys():
        sheet_name_inside = str(list(topics.keys()).index(sheet_name) + 1)
        topics[sheet_name].to_excel(writer, sheet_name=sheet_name_inside)

        worksheet = writer.sheets[sheet_name_inside]
        worksheet.set_column('A:A', 5, wrap_format)
        worksheet.set_column('B:B', 50, wrap_format)
        worksheet.set_column('C:C', 25, wrap_format)
        worksheet.set_column('D:D', None, None, {'hidden': True})
        worksheet.set_column('E:E', None, None, {'hidden': True})
        worksheet.set_column('F:K', 27, wrap_format)
        (max_row, max_col) = topics[sheet_name].shape
        format1 = workbook.add_format({'bold': 1, 'bg_color': '#7FFF00'})
        worksheet.conditional_format(0, 5, max_row, 10, {'type': 'formula',
                                                         'criteria': '=IF(HLOOKUP($D1,F$1,1,FALSE)=$D1,TRUE,FALSE)',
                                                         'format': format1})

    writer.close()


if __name__ == '__main__':
    transfer_data()
