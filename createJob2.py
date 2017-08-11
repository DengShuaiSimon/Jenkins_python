from __future__ import print_function
###from pkg_resources import resource_string
from jenkinsapi.jenkins import Jenkins
from jenkinsapi.job import Job
from jenkinsapi.views import Views   ##for nested view
import logging
import xml.etree.ElementTree as ET
#import ConfigParser 
import string,os,sys
import fileinput 

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger()



###############get information from jenkins_project.conf#############
def getDicFromConf(path):
	conf_arr = []
	bundle_arr = []
	conf_dic = {}###the dic for storing the key-value of the conf array 
	kv_arr = []
	for line in fileinput.input("jenkins_project.conf"):
		line=line.strip()
		index = line.find('#')
		if line == '' or index == 0:
			continue;
		elif index == -1:
			#print('index:',index)
			conf_arr.append(line)
		else:
			line = line[0:index]; line= line.strip(); conf_arr.append(line);
			#print(line);
			
	#print(conf_arr);
	
	begin = 0;
	end = len(conf_arr)-1;
	new_len = len(conf_arr);
	#print('len:',len(conf_arr))
	isbundle = 0  ##Record if there is the bundle 
	isplugin = 0
	for i in range(0,len(conf_arr)):
		if conf_arr[i]=="[customize_bundle]":
			begin=i
			isbundle=1
			new_len = begin+1
	for i in range(0,len(conf_arr)):
		if ('customize_plugin' in conf_arr[i] and isbundle):
			isplugin=1
			end=i-1;
			new_len=new_len+1

	#print('begin:',begin,'end:',end,'new_len:',new_len,'isbundle:',isbundle)

	if isbundle:
		for j in range(begin+1,end+1):
			bundle_arr.append(conf_arr[j])
		for k in range(0,new_len):
			if k == begin:
				conf_dic[conf_arr[begin]]= bundle_arr
			elif k > begin:
				str=conf_arr[end+1]
				kv_arr = str.split('=')
				str1=kv_arr[0]
				str2=kv_arr[1]
				str1=str1.strip()
				str2=str2.strip()
				conf_dic[str1]=str2
			else:
				str = conf_arr[k]
				kv_arr = str.split('=')
				str1=kv_arr[0]
				str2=kv_arr[1]
				str1=str1.strip()
				str2=str2.strip()
				conf_dic[str1]=str2
	else: 
		for k in range(0,new_len):
			str = bundle_arr[k]
			kv_arr = str.split('=')
			str1=kv_arr[0]
			str2=kv_arr[1]
			str1=str1.strip()
			str2=str2.strip()
			conf_dic[str1]=str2
	print('conf_dic:',conf_dic,'\n','conf_dic_len:',len(conf_dic),'\n')
	return conf_dic

def create_job_by_conf(conf_file,config_xml_name):
	conf_dic = getDicFromConf(conf_file)#"jenkins_project.conf"

	######connect jenkins and initial#########
	'''
	if 'jenkins_master' in conf_dic.keys():
		jenkins_url = 'http://'+conf_dic['jenkins_master']+':8080'
		jenkins = Jenkins(jenkins_url,username="admin",password="cluster")
	else:
		print('Please set jenkins_master in jenkins_project.conf.')
	'''

	if 'project_name' in conf_dic.keys():
		job_name = conf_dic['project_name']
	else:
		print('Please set project_name in jenkins_project.conf.\n')

	if 'group_name' in conf_dic.keys():
		test_view_name = conf_dic['group_name']
	else:
		print('Please set group_name in jenkins_project.conf.\n')
	
	if 'test_cluster' in conf_dic.keys():
		assignedNode = conf_dic['test_cluster']
	else:
		print('Please set test_cluster in jenkins_project.conf.\n')

	if 'build_schedule' in conf_dic.keys():
		str = conf_dic['build_schedule']
		timerTrigger_text = 'H '+ str + ' * * *'
	else:
		print('Please set build_schedule in jenkins_project.conf.\n')

	if 'os' in conf_dic.keys():
		XCAT_TEST_OS = conf_dic['os']
	else:
		#raise Exception("Please set os in jenkins_project.conf.\n!")
		print('Please set os in jenkins_project.conf.\n')

	'''
	if 'arch' in conf_dic.keys():
		arch = conf_dic['arch']
	else:
		print('Please set arch in jenkins_project.conf.')
	'''
	XCAT_TEST_BRANCH_OR_CORE = ''
	if ('branch' in conf_dic.keys() and 'customize_xcat_core' in conf_dic.keys()):
		#raise Exception("Branch and XCAT_TEST_CORE are conflicting.Please reset the configuration file.\n")
		print('Branch and XCAT_TEST_CORE are conflicting.Please reset the configuration file.\n')	
	elif 'branch' in conf_dic.keys():
		branch_str = conf_dic['branch']
		XCAT_TEST_BRANCH_OR_CORE = '#---------To spcify target xcat build---------\n\n#If need to test your own build.\n#comment "XCAT_TEST_BRANCH" line out,move "#" out of below "XCAT_TEST_CORE" line and set corect value\n#if need to test the latest daily build in build server,\n#comment "XCAT_TEST_CORE" line out,move "#" out of below "XCAT_TEST_BRANCH" line and set corect value\n#for example : master or 2.13\n\nexport XCAT_TEST_BRANCH=%s\n\n' % (branch_str)
	elif 'customize_xcat_core' in conf_dic.keys():
		core_str = conf_dic['customize_xcat_core']
		XCAT_TEST_BRANCH_OR_CORE = '#---------To spcify target xcat build---------\n\n#If need to test your own build.\n#comment "XCAT_TEST_BRANCH" line out,move "#" out of below "XCAT_TEST_CORE" line and set corect value\n#if need to test the latest daily build in build server,\n#comment "XCAT_TEST_CORE" line out,move "#" out of below "XCAT_TEST_BRANCH" line and set corect value\n#for example : master or 2.13\n\nexport XCAT_TEST_CORE=%s\n\n\n' % (core_str)
	else:
		print('Please set customize_xcat_core or branch in jenkins_project.conf.\n')

	if 'customize_xcat_dep' in conf_dic.keys():
		dep_str = conf_dic['customize_xcat_dep']
		XCAT_TEST_DEP = '#---------To spcify target xcat dependency package---------\n\n#If not set, will use the latest dependency package in xcat.org\nexport XCAT_TEST_DEP=%s\n\n' % (dep_str)
	else:
		XCAT_TEST_DEP = ''
		print('Here didn\'t set customize_xcat_dep in jenkins_project.conf.\n')

	development = '#For automation development environment, using below 2 line  [RECOMMEND]\nexport XCAT_TEST_GIT_REPO=git@github.ibm.com:gongjie/jenkins.git\nexport XCAT_TEST_GIT_BRANCH=devel\n\n';
	product = '#For automation product environment, using below 2 line  [NOT RECOMMEND]\nexport XCAT_TEST_GIT_REPO=git@github.ibm.com:xcat2/jenkins.git\nexport XCAT_TEST_GIT_BRANCH=master\n\n\n';#####Now firstly code commenting in production 
	if 'automation_env' in conf_dic.keys():
		env = conf_dic['automation_env']
		if env == 'development':
			AUTOMATION_ENV = development
			jenkins_url = 'http://127.0.0.1:8080' #'http://10.2.4.25:8080'
			jenkins =  Jenkins(jenkins_url,username="dengshuai_super",password="8080") #Jenkins(jenkins_url,username="admin",password="cluster")
		elif env == 'production':
			AUTOMATION_ENV = product
			jenkins_url = 'http://10.4.32.1:8080'
			jenkins = Jenkins(jenkins_url,username="admin",password="cluster")
	else:
		print('Please set automation_env in jenkins_project.conf.\n')

	if 'mailing_list' in conf_dic.keys():
		mailing_str = conf_dic['mailing_list']
		XCAT_TEST_MAILING_LIST = '#---------To specify mailing list ---------\n#using comma to separate different people\nexport XCAT_TEST_MAILING_LIST=%s\n\n' % (mailing_str)
	else:
		XCAT_TEST_MAILING_LIST = ''
		print('Here didn\'t set mailing_list in jenkins_project.conf.')

	if 'database' in conf_dic.keys():
		database_str = conf_dic['database']
		XCAT_TEST_DATABASE = '#---------To specify the database type----------\n\n#Using Mysql by default\nexport XCAT_TEST_DATABASE=%s\n\n' % (database_str)
	else:
		XCAT_TEST_DATABASE = ''
		print('Here didn\'t set database in jenkins_project.conf.')



	bundles_str = ''
	if '[customize_bundle]' in conf_dic.keys():
		bundle_arr = conf_dic['[customize_bundle]']
		for bundle in bundle_arr:
			bundles_str = bundles_str + bundle + '\n';
		
		BUNDLE_STR = '#---------To specify test case list ---------\n\n#If need to customize you own case list,\n#paste you case in bundle array\ndeclare -a bundle=(\n%s)\nexport XCAT_TEST_CASE="${bundle[*]}"\n\n' % (bundles_str);
	else:
		BUNDLE_STR = ''
		print('Here didn\'t set [customize_bundle] in jenkins_project.conf.')

	if 'customize_plugin' in conf_dic.keys():
		plugin_str = conf_dic['customize_plugin']
		XCAT_TEST_PLUGIN = '#---------To specify the additional plugin----------\n\n#using this attribute to specify some customize script which\'s result will be inserted into normal mail report\n#The plugin script should be check in Jenkins repo "~/jenkins/plugin" ahead.\nexport XCAT_TEST_PLUGIN=%s\n\n' % (plugin_str)
	else:
		XCAT_TEST_PLUGIN = ''
		print('Here didn\'t set customize_plugin in jenkins_project.conf.')

	command_text='#!/bin/bash\n\nset -x\n\n#---------To spcify OS wanted to run whole test based on---------\n\n#[naming rule]:\n#The os name should be consistent with the os name which xcat copycds generated.\n#Take redhat7.3 for example,the osimage name is rhels7.3-ppc64le-install-compute,\n#the value of XCAT_TEST_OS should be rhels7.3\nexport XCAT_TEST_OS=%s\n\n\n%s%s#---------To spcify automation framework code repo---------\n\n%s%s%s%s\n%s#----------------DO NOT MODIFY BELOW LINES-------------\n\ncp /tmp/dengshuai/test.sh .\n./test.sh' % (XCAT_TEST_OS,XCAT_TEST_BRANCH_OR_CORE,XCAT_TEST_DEP,AUTOMATION_ENV,XCAT_TEST_MAILING_LIST,BUNDLE_STR,XCAT_TEST_DATABASE,XCAT_TEST_PLUGIN)


	##############set configure xml from jenkins_project.conf############
	'''
	job_name = pass
	assignedNode = pass
	timerTrigger_text = pass
	command_text = pass
	'''

	'''#get the config.xml from a template project
	template_job_name = "ds_project_template"#"test8"#"ds_project_template"
	config_xml_name = "config.xml"##"project_xml_template.xml"
	config = jenkins[template_job_name].get_config()
	f = open(config_xml_name,'w')
	f.write(config)
	f.close()
'''
	#config_xml_name = "config.xml"
	tree = ET.parse(config_xml_name)###"config.xml"
	root = tree.getroot()
	#root.find('assignedNode').text = assignedNode
	node = root.find('assignedNode')
	if node is None:
		node = ET.SubElement(root,'assignedNode')
	node.text = assignedNode
	
	triggers = root.find('triggers')
	timerTrigger = triggers.find('hudson.triggers.TimerTrigger')
	if timerTrigger is None:
		timerTrigger = ET.SubElement(triggers,'hudson.triggers.TimerTrigger')
	spec = timerTrigger.find('spec')
	if spec is None:
		spec = ET.SubElement(timerTrigger,'spec')
	spec.text = timerTrigger_text
	
	builders = root.find('builders')
	if builders is None:
		builders = ET.SubElement(root,'builders')
	shell = builders.find('hudson.tasks.Shell')
	if shell is None:
		shell = ET.SubElement(builders,'hudson.tasks.Shell')
	command = shell.find('command')
	if command is None:
		command = ET.SubElement(shell,'command')
	command.text = command_text
	xml = ET.tostring(root).decode('utf-8')
	'''
	config_output_name = "config_output.xml"
	tree.write(config_output_name,xml_declaration=True, encoding='utf-8', method="xml")
'''

	#job_name = 'ds_project_test1'#foo_job1
	###xml = resource_string('examples', 'addjob.xml')
	#xml = open('./addjob.xml',encoding='utf8').read()
	#xml = open(config_output_name).read()
	if job_name in jenkins.jobs:
		logger.info('the job named '+job_name+' already exists')
	else:
		job = jenkins.create_job(jobname=job_name, xml=xml);


def create_empty_job_from_string(projectname):
	conf_str ='''<?xml version='1.0' encoding='UTF-8'?>
<project>
  <actions/>
  <description></description>
  <keepDependencies>false</keepDependencies>
  <properties/>
  <scm class="hudson.scm.NullSCM"/>
  <canRoam>true</canRoam>
  <disabled>false</disabled>
  <blockBuildWhenDownstreamBuilding>false</blockBuildWhenDownstreamBuilding>
  <blockBuildWhenUpstreamBuilding>false</blockBuildWhenUpstreamBuilding>
  <triggers class="vector"/>
  <concurrentBuild>false</concurrentBuild>
  <builders/>
  <publishers/>
  <buildWrappers/>
</project>'''
	if projectname in jenkins.jobs:
		logger.info('the job '+projectname+' already exists')
	else:
		job = jenkins.create_job(jobname=projectname,xml=conf_str)




def change_Schedule(jenkins,projectname,time_str):
	job = jenkins[projectname]
	conf = job.get_config()
	root = ET.fromstring(conf.strip())
	triggers = root.find('triggers')
	timerTrigger = triggers.find('hudson.triggers.TimerTrigger')
	if timerTrigger is None:
		timerTrigger = ET.SubElement(triggers,'hudson.triggers.TimerTrigger')
	spec1 = timerTrigger.find('spec')
	if spec1 is None:
		spec1 = ET.SubElement(timerTrigger,'spec')
	spec1.text = time_str
	conf_str = ET.tostring(root).decode('utf-8')
	job.update_config(conf_str)
	#tree1 = ET.ElementTree(root)
	#tree1.write('new1.xml',xml_declaration=True, encoding='utf-8', method="xml")

def change_Assigned_Node(jenkins,projectname,node_str):
	job = jenkins[projectname]
	conf = job.get_config()
	root = ET.fromstring(conf.strip())
	node = root.find('assignedNode')
	if node is None:
		node = ET.SubElement(root,'assignedNode')
	node.text = node_str
	conf_str = ET.tostring(root).decode('utf-8')
	job.update_config(conf_str)
	#tree1 = ET.ElementTree(root)
	#tree1.write('new1.xml',xml_declaration=True, encoding='utf-8', method="xml")

def change_Description(jenkins,projectname,description_str):
	job = jenkins[projectname]
	conf = job.get_config()
	root = ET.fromstring(conf.strip())
	des = root.find('description')
	if des is None:
		des = ET.SubElement(root,'description')
	des.text = description_str
	conf_str = ET.tostring(root).decode('utf-8')
	job.update_config(conf_str)
	#tree1 = ET.ElementTree(root)
	#tree1.write('new1.xml',xml_declaration=True, encoding='utf-8', method="xml")
	

def change_Command(jenkins,projectname,command_str):
	job = jenkins[projectname]
	conf = job.get_config()
	root = ET.fromstring(conf.strip())
	builders = root.find('builders')
	if builders is None:
		builders = ET.SubElement(root,'builders')
	shell = builders.find('hudson.tasks.Shell')
	if shell is None:
		shell = ET.SubElement(builders,'hudson.tasks.Shell')
	command = shell.find('command')
	if command is None:
		command = ET.SubElement(shell,'command')
	command.text = command_str
	conf_str = ET.tostring(root).decode('utf-8')
	job.update_config(conf_str)



def change_group_jobs_schedule(jenkins,group_name,timer_str):
	if group_name in jenkins.views:
		for job in jenkins.views[group_name].items():
			print(job[0])
			change_Schedule(jenkins,job[0],timer_str)##job[0]===>the name of job
	else:
		#logger.info('View has been deleted')
		logger.error(group_name+' is not in jenkins.\n')


if __name__ == '__main__':
	jenkins_url = 'http://127.0.0.1:8080' #'http://10.2.4.25:8080'
	jenkins =  Jenkins(jenkins_url,username="dengshuai_super",password="8080") 
	
	create_job_by_conf("jenkins_project.conf","config.xml")
	change_Description(jenkins,"test9","I have change the description of test9!")
	change_Assigned_Node(jenkins,"test9","12345")
	change_Schedule(jenkins,"test9","H 9 * * *")
	change_Command(jenkins,"test9","dir\n")
	
	create_empty_job_from_string("test7")
	change_Description(jenkins,"test7","I have change the description of test8!")
	change_Assigned_Node(jenkins,"test7","12345")
	change_Schedule(jenkins,"test7","H 2 * * *")
	change_Command(jenkins,"test7","dir")
	
	change_group_jobs_schedule(jenkins,"ds_group2","H 8 * * *")
	

'''
###build a job,params is optional
params = {'VERSION': '1.2.3', 'PYTHON_VER': '2.7'}
#jenkins.build_job(job_name,params)


# This will start the job in non-blocking manner
jenkins.build_job('foo', params)


# This will start the job and will return a QueueItem object which
# can be used to get build results
job = jenkins['foo']
qi = job.invoke(build_params=params) ##params can be None.

# Block this script until build is finished
if qi.is_queued() or qi.is_running():
    qi.block_until_complete()

build = qi.get_build()
print(build)
'''

'''
# Get job from Jenkins by job name
my_job = jenkins[job_name]
print(my_job)

# Delete job using method in Jenkins class
#
# Another way is to use:
#
# del jenkins[job_name]
#jenkins.delete_job(job_name)

# Create ListView in main view
logger.info('Attempting to create new view')
#test_view_name = 'ds_group2'#SimpleListView1
my_view = jenkins.views.create(test_view_name)
my_view.add_job(job_name, my_job)

#assert len(my_view) == 1   ##len(my_view) can get the number of jobs in the view

#logger.info('Attempting to delete view that already exists')
#del jenkins.views[test_view_name]

#if test_view_name in jenkins.views:
#    logger.error('View was not deleted')
#else:
#    logger.info('View has been deleted')


for job in jenkins.views[test_view_name].items():
     print(job)
'''
###python createJob.py -g group2 -s "H 6 * * *"/disable
###python createJob.py -p project_name
