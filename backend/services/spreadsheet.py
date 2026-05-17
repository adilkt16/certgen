import csv
import io
import openpyxl


def parse_spreadsheet(file_bytes, filename):
	name = filename.lower()
	if name.endswith('.csv'):
		text = file_bytes.decode('utf-8')
		f = io.StringIO(text)
		reader = csv.DictReader(f)
		rows = []
		for row in reader:
			if all((v is None) or (str(v).strip() == '') for v in row.values()):
				continue
			rows.append(row)
		return rows

	if name.endswith('.xlsx'):
		wb = openpyxl.load_workbook(io.BytesIO(file_bytes), data_only=True)
		ws = wb.worksheets[0]
		rows = []
		iterator = ws.iter_rows(values_only=True)
		try:
			header = next(iterator)
		except StopIteration:
			return []
		headers = [str(h) if h is not None else '' for h in header]
		for r in iterator:
			if all((c is None) or (str(c).strip() == '') for c in r):
				continue
			row = {headers[i]: r[i] for i in range(len(headers))}
			rows.append(row)
		return rows

	raise ValueError("Only .csv and .xlsx files are supported")


def get_column_names(rows):
	if not rows:
		return []
	first = rows[0]
	return list(first.keys())


def get_names(rows, column):
	names = []
	for row in rows:
		val = row.get(column)
		if val is None:
			continue
		s = str(val).strip()
		if s:
			names.append(s)
	return names

