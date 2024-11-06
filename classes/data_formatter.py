# data_formatter.py
from .utils import log

class DataFormatter:
    def __init__(self, config):
        self.config = config

    def format_data(self, data):
        if not data:
            return data
        for source in data:
            if not data:
                continue
            format_source = self.config.get(source, {}).get('formatters', {})
            if  not format_source:
                return data
            for format in format_source:
                method = format.get('method')
                settings = format.get('settings')
                if not method or not hasattr(self, method):
                    log(f"Method not set, or not defined", 'warning')
                    log(f"Method: {method}", 'debug')
                    continue
                try:
                    prop = format.get('property')
                    data = getattr(self, method)(data, source, prop, settings)
                except Exception as e:
                    log(f"An error occured in {method}", 'warning')
                    log(str(e), 'debug')
        return data
    
    def append_data(self, data, source, prop, formatted):
        if not formatted:
            return data
        if source not in data:
            data[source] = {}
        data[source][prop+'_formatted'] = formatted
        return data

    def limit_line_length(self, data, source, prop, settings):
        lines = []
        text = data.get(source, {}).get(prop, None)
        if not text:
            return data
        max_length = settings.get('max_length', 125)
        while len(text) > max_length:
            wrap_at = text.rfind(' ', 0, max_length)
            if wrap_at == -1:
                wrap_at = max_length
            lines.append(text[:wrap_at].strip())
            text = text[wrap_at:].strip()
        lines.append(text)
        formatted = '\n'.join(lines)
        return self.append_data(data, source, prop, formatted)