import datetime

import pandas as pd

from connect import client
from const import BREAKS


def get_data(worksheet):
    bt = worksheet.worksheet('Plan odwożenia').get_all_records()
    bt = pd.DataFrame(bt)
    bt['trasa'] = bt['trasa'].apply(lambda x: x.split(', '))

    st = worksheet.worksheet('Jak klasy kończą lekcje').get('A2:U7')
    st = pd.DataFrame(st)
    st.columns = st.iloc[0]
    st = st[1:]

    sl = worksheet.worksheet('Ilość dzieci odwożonych').get_all_records()
    sl = pd.DataFrame(sl)

    return bt, st, sl


def prepare_df_number_students_from_location(timetable, location):
    number_of_lessons = timetable.melt('dzień', timetable.columns[1:])
    number_of_lessons.columns = ['dzień', 'klasa', 'liczba_lekcji']

    locations_students_by_class = location.melt('klasa', location.columns[1:-1])
    locations_students_by_class.columns = ['klasa', 'lokalizacja', 'liczba_dzieci']

    students_from_location = pd.merge(number_of_lessons, locations_students_by_class, on='klasa')
    students_from_location = students_from_location[students_from_location['liczba_dzieci'] != 0]
    students_from_location['liczba_lekcji'] = students_from_location['liczba_lekcji'].map(BREAKS)

    return students_from_location


def list_to_tuple(df, column):
    df[column] = df[column].apply(lambda x: tuple(x))
    return df


def list_to_str(df, column):
    df[column] = df[column].str.join(", ")
    return df


def select_first(df, group_by_list):
    df = df[df['godz'] >= df['liczba_lekcji']]
    df = df.sort_values('godz')
    df = df.groupby(group_by_list).first().reset_index()
    return df


def select_bus(students_from_location, buses):
    students_in_buses = pd.merge(students_from_location, buses, on='dzień')
    # TODO; pozostale dzieci
    students_in_buses = students_in_buses[students_in_buses.apply(lambda row: row.lokalizacja in row.trasa, axis=1)]
    students_in_buses = students_in_buses[students_in_buses['liczba_dzieci'] != '']
    students_in_buses = select_first(students_in_buses, ['dzień', 'klasa', 'lokalizacja'])
    students_in_buses = list_to_tuple(students_in_buses, 'trasa')

    selected_data = students_in_buses[['dzień', 'godz', 'trasa', 'klasa', 'liczba_dzieci']]
    selected_data = selected_data.groupby(['dzień', 'godz', 'trasa', 'klasa'])['liczba_dzieci'].sum().reset_index()
    selected_data['klasa_dzieci'] = selected_data["klasa"].map(str) + ": " + selected_data["liczba_dzieci"].map(str)
    selected_data = selected_data.groupby(['dzień', 'godz', 'trasa']).apply(
        lambda x: [list(x['klasa_dzieci']), sum(x['liczba_dzieci'])]).apply(pd.Series)
    selected_data = selected_data.reset_index()
    selected_data = list_to_str(selected_data, 'trasa')
    return selected_data


if __name__ == '__main__':
    start = datetime.datetime.now()
    worksheet_instance = client.open('Odwożenie')
    bus_timetable, students_timetable, students_location = get_data(worksheet_instance)

    num_stud_from_loc = prepare_df_number_students_from_location(students_timetable, students_location)

    selected_bus = select_bus(num_stud_from_loc, bus_timetable)

    bus_timetable = list_to_str(bus_timetable, 'trasa')
    selected_bus = pd.merge(bus_timetable, selected_bus, on=['dzień', 'godz', 'trasa'])
    selected_bus.pop('liczba dzieci z klas')
    selected_bus.pop('suma dzieci')
    selected_bus.columns = ['dzień', 'godz', 'trasa', 'liczba dzieci z klas', 'suma dzieci']
    selected_bus = list_to_str(selected_bus, 'liczba dzieci z klas')

    test = worksheet_instance.worksheet('test')
    test.update([selected_bus.columns.values.tolist()] + selected_bus.values.tolist())

    end = datetime.datetime.now()
    print(end)
    print(end - start)
