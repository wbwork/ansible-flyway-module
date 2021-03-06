#!/usr/bin/python
import re

ANSIBLE_METADATA = {
  'metadata_version': '1.1',
  'status': ['preview'],
  'supported_by': 'community'
}

DOCUMENTATION = '''
---
module: flyway

short_description: Make flyway available for ansible as a module to have a changed status available

description:
    - "This is my longer description explaining my sample module"

options:
    cmd:
        description:
            - the command to execute
        required: true
    url:
        description:
            - url to access the database
        required: true
    user:
        description:
            - the user to connect with
        required: false
    password:
        description:
            - the password to connect with
        required: false

author:
    - Wolfgang Bauer
'''

EXAMPLES = '''
# Create baseline
- name: baseline
  flyway:
    cmd: baseline
    user: root
    url: jdbc:mysql://localhost:3306/
    schemas: sample-db

# 
- name: Retrieve executed migrations
  flyway:
    cmd: info
    user: root
    url: jdbc:mysql://localhost:3306/
    schemas: sample-db

# fail the module
- name: Execute migrations
  flyway:
    cmd: migrate
    user: root
    url: jdbc:mysql://localhost:3306/
    schemas: sample-db
'''

RETURN = '''
TODO: add return info
'''

from ansible.module_utils.basic import AnsibleModule


def baseline(module, cmd, result):

  # create baseline

  c, out, err = module.run_command(cmd)
  if c == 1:
    if "as it already contains migrations" in err:
      result['changed'] = False
      result['message'] = "Database containing already migrations (without baseline)"
    else:
      module.fail_json(msg='Creating baseline failed', error=err)
  else:
    if "Skipping" in out:
      result['changed'] = False
    else:
      result['changed'] = True
    result['message'] = out
  return result


def info(module, cmd, result):
  # show info as debug
  c, out, err = module.run_command(cmd)
  if c == 1:
    module.fail_json(msg='Retrieving info failed', error=err)
  if "No migrations found" in out:
    result['message'] = 'no migration'
    result['entries'] = []
  else:
    lines = out.split("\n")

    entries = []
    for l in lines:
      if "|" in l:
        m = re.split("\s*\|\s*", l)
        data = dict(version=m[1], description=m[2], installed_on=m[3],
                    state=m[4])
        if data["version"] != "Version":
          entries.append(data)
          result["last_version"] = data["version"]
    result["entries"] = entries
    return result

  return result

def validate(module, cmd, result):
  c, out, err = module.run_command(cmd)
  if c==1:
    if "Detected resolved migration not applied to database" in err:
      result["missed_migration"] = re.search("database: ([0-9]*\.[0-9]*)\\n",err).group(1)
    result["error"] = True
    result["error_msg"] = err
  else:
    result["error"] = False
    result["out"] = out
    m = re.search("Successfully validated ([0-9]+) migrations",out)
    if m:
      result["migrations"] = m.group(1)

  return result

def migrate(module, cmd, result):
  # execute migration
  c, out, err = module.run_command(cmd)

  if c == 1:
    # migration failed
    result["error"] = True
    result["error_msg"] = err
    module.fail_json(msg='Migration failed', error=result["error_msg"])

  if "No migration necessary" in out:
    result["changed"] = False
  else:
    result["changed"] = True
    lines = out.split("\n")

    entries = []
    for l in lines:
      if "Migrating schema " in l:
        m = re.match("to version ([0-9\.]*) - (\w*)",l)
        data = dict(version=m[0], description=m[1])
        entries.append(data)
        result["latest_version"] = data["version"]
    result["entries"] = entries
  result["out"] = out
  return result


def run_module():
  # define the available arguments/parameters that a user can pass to
  # the module
  module_args = dict(
      cmd=dict(type='str', required=True),
      url=dict(type='str', required=True),
      user=dict(type='str', required=False, default='root'),
      password=dict(type='str', required=False, default='', no_log=True),
      executable=dict(type='str', required=False, default='flyway'),
      locations=dict(type='str', required=False),
      schemas=dict(type='str', required=False),
      outOfOrder=dict(type='bool', required=False, default=True),
      cleanDisabled=dict(type='bool', required=False, default=True)
  )

  # seed the result dict in the object
  result = dict(
      changed=False
  )

  # the AnsibleModule object will be our abstraction working with Ansible
  # this includes instantiation, a couple of common attr would be the
  # args/params passed to the execution, as well as if the module
  # supports check mode
  module = AnsibleModule(
      argument_spec=module_args,
      supports_check_mode=True
  )

  executable = module.params["executable"]

  if 'schemas' not in module.params and re.match("\w+:\w+://[a-zA-Z0-9]+:\d+/\w+", module.params['url']) is None:
    module.fail_json(msg='No schema defined by parameter schemas or by url')
  options = ("-user=%s -password=%s -url=%s") % (
    module.params['user'], module.params['password'], module.params['url'])
  if 'locations' in module.params:
    options += (" -locations=%s") % (module.params['locations'])
  if 'schemas' in module.params:
    options += (" -schemas=%s") % (module.params['schemas'])
  cmd = ("%s %s %s") % (executable, options, module.params['cmd'])
  if module.params['cmd'] == 'baseline':
    result = baseline(module, cmd, result)
  if module.params['cmd'] == 'info':
    result = info(module, cmd, result)
  if module.params['cmd'] == 'migrate':
    result = migrate(module, cmd, result)
  if module.params['cmd'] == 'validate':
    result = validate(module, cmd, result)
    if result["error"]:
      module.fail_json(msg='Validate failed', error=result["error_msg"],missed_migration=result["missed_migration"])

  module.exit_json(**result)


def main():
  run_module()


if __name__ == '__main__':
  main()
