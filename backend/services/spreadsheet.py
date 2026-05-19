import csv
import io
import re
import openpyxl

# Import font manager to get valid font list
try:
	if __name__ != "__main__":
		from . import font_manager
except ImportError:
	font_manager = None


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


def _sanitize_cell(val):
	"""Strip leading =, +, -, @ from cell values to prevent CSV injection."""
	s = str(val).strip()
	s = re.sub(r'^[=+\-@]', '', s)
	return s


def get_names(rows, column):
	"""Extract and sanitize names from a specific column."""
	names = []
	for row in rows:
		val = row.get(column)
		if val is None:
			continue
		s = _sanitize_cell(val)
		if s:
			names.append(s)
	return names


def get_valid_fonts():
	"""Get the list of valid/allowlisted font names."""
	if font_manager:
		return font_manager.get_font_list()
	return []

