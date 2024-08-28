import os

class Config:
    def __init__(self):
        self.config = {}
        config_path = os.path.join(os.path.dirname(__file__), 'config.ini')
        self._load_config(config_path)

    def _load_config(self, config_path):
        current_section = None
        with open(config_path, 'r') as f:
            for line in f:
                line = line.strip()
                
                # Skip empty lines and comments
                if not line or line.startswith('#'):
                    continue
                
                if line.startswith('[') and line.endswith(']'):
                    current_section = line[1:-1]
                    self.config[current_section] = {}
                elif '=' in line and current_section is not None:
                    key, value = line.split('=', 1)
                    key = key.strip()
                    # Process value as a raw string
                    value = r'{}'.format(value.split('#')[0].strip())
                    self.config[current_section][key] = value

    def get(self, section, key):
        return self.config.get(section, {}).get(key)

# Create a global instance
config = Config()

# Convenience function
def path(key):
    key_path = config.get('paths', key)
    if key_path:
        return key_path
    raise KeyError('No path specified in config.ini')

if __name__ == '__main__':
    print(config.config)
    