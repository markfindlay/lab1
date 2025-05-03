# lab1

Workaround for hostvars & groupvars outside of auto generated clab folder
```bash
cd lab1
ln -s ansible-inventory.yml clab-topology.clab/ansible-inventory.yml
```

Create a venv & install requirements
```bash
cd lab1
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

Optional - symlink ez.py to usr/local/bin so you can type 'ez' from the cli.
```bash
sudo ln -s ~/lab1/ez.py /usr/local/bin/ez
```

Restore config
```bash
ez restore
```

Backup config
```bash
ez backup
```

Run predefined commands with structured output
```bash
ez show version
```

Run arbitrary commands
```bash
ez run 'show system uptime'
```
