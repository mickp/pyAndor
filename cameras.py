## _cameras [(label, dsp line, ip address, model)]
cameras = [
    ('West', 9146, 1<<0, '192.168.1.2', 7777, 'ixon', ['GFP', 'mCherry'], [525, 585]),
    ('East', 9145, 1<<1, '192.168.1.2', 7778, 'ixon', ['Cy5', 'FITC'], [670, 518]),
    ]
camera_keys = ['label', 'serial', 'line', 'ipAddress', 'port', 'model', 'dyes', 'wavelengths']
