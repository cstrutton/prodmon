The config file is in yaml format.

It is a list of devices:

Each device has its connection parameters and a list of Tags to retrieve from that device.
```yaml
device:
  - type: [pylogix|modbus]      # which driver to use
    ip: [xx.xx.xx.xx]           # ip address
    processor_slot: [x]         # Optional: slot number for pylogix PLC's 
    frequency: .5               # maximum polling frequency in seconds
    tags:
      - tag: ... 
```
Each tag:
```yaml
    tags:
      # pylogix counter tag
      - type: 'counter' 
        tag: 'tagname'          # the full path to the tag in the PLC
        scale: 1                # how many parts per cycle
        part_number: '50-9341'  # recorded in the part_number column in the db
        machine: '728'          # recorded in the machine column in the db
        table: 'GFxPRoduction'  # database table to write to
      # pylogix data tag (pending)
      - type: 'data'
        tag: 'tagname'
        scale: 1                # scale from machine to engineering units
        name: 'droptimer'       # recorded in the name column in the db
        table: 'datatable'      # db table to write value to
        strategy: 'on_change'   # when to record to db: always|on_change
      # modbus register
      - type: 'ADAM_counter'    # reads ADAM 6xxx counter register
        register: 16            # register to start reading from
        scale: 1                # number of parts per cycle
        part_number: '50-9341'  # recorded in the part_number column in the db
        machine: '650L'         # recorded in the machine column in the db
        table: 'GFxPRoduction'  # database table to write to
```

