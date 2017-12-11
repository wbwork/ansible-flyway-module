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

extends_documentation_fragment:
    - azure

author:
    - Your Name (@yourhandle)
'''

EXAMPLES = '''
# Pass in a message
- name: Test with a message
  my_new_test_module:
    name: hello world

# pass in a message and have changed true
- name: Test with a message and changed output
  my_new_test_module:
    name: hello world
    new: true

# fail the module
- name: Test failure of the module
  my_new_test_module:
    name: fail me
'''

RETURN = '''
TODO: add return info
'''

from ansible.module_utils.basic import AnsibleModule

def baseline(module, executable, result):
    # create baseline
    options = ("-user=%s -password=%s -url=%s") % (module.params['user'],module.params['password'], module.params['url'])
    cmd = ("%s %s baseline") % (executable, options)
    c, out, err = module.run_command(cmd)
    if c==1:
        module.fail_json(msg='Creating baseline failed',error=err)
    result['changed'] = c==0
    result['message'] = out
    return result

def info(module, executable, result):
    # show info as debug
    options = ("-user=%s -password=%s -url=%s") % (module.params['user'],module.params['password'], module.params['url'])
    cmd = ("%s %s info") % (executable, options)
    c, out, err = module.run_command(cmd)
    if c==1:
        module.fail_json(msg='Retrieving info failed',error=err)
    if "No migrations found" in out:
        result['message']= 'no migration'
    else:
        lines = out.split("\n")

        entries = []
        for l in lines:
            if "|" in l:
                m = re.split("\s*\|\s*",l)
                data = dict(version=m[1],description=m[2],installed_on=m[3],state=m[4])
                if data["version"] != "Version":
                    entries.append(data)
        result["entries"]=entries
        return result

    return result

def migrate():
    # execute migration
    return

def run_module():
    # define the available arguments/parameters that a user can pass to
    # the module
    module_args = dict(
        cmd=dict(type='str', required=True),
        url=dict(type='str', required=True),
        user=dict(type='str', required=False, default='root'),
        password=dict(type='str', required=False, default=''),
        executable=dict(type='str', required=False, default='flyway')
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
    if module.params['cmd'] == 'baseline':
        result = baseline(module, executable, result)
    if module.params['cmd'] == 'info':
        result = info(module, executable, result)

    # if the user is working with this module in only check mode we do not
    # want to make any changes to the environment, just return the current
    # state with no modifications
    if module.check_mode:
        return result

    # in the event of a successful module execution, you will want to
    # simple AnsibleModule.exit_json(), passing the key/value results
    module.exit_json(**result)

def main():
    run_module()

if __name__ == '__main__':
    main()
