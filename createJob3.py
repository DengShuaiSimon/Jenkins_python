from __future__ import print_function
###from pkg_resources import resource_string
from jenkinsapi.jenkins import Jenkins
from jenkinsapi.job import Job
from jenkinsapi.views import Views   ##for nested view
import logging
import xml.etree.ElementTree as ET
#import ConfigParser 
import string,os,sys,getopt
import fileinput 

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger()



###############get information from jenkins_project.conf#############
def getDicFromConf(path):
	conf_arr = []
	bundle_arr = []
	conf_dic = {}###the dic for storing the key-value of the conf array 
	kv_arr = []
	for line in fileinput.input(path):#"jenkins_project.conf"
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

def get_Xml_From_Conf_And_Template_Xml(conf_file):
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
	config_string='''<project>
<description>I have change the description of test8!</description>
<keepDependencies>false</keepDependencies>
<properties/>
<scm class="hudson.scm.NullSCM"/>
<canRoam>true</canRoam>
<disabled>false</disabled>
<blockBuildWhenDownstreamBuilding>false</blockBuildWhenDownstreamBuilding>
<blockBuildWhenUpstreamBuilding>false</blockBuildWhenUpstreamBuilding>
<triggers>
<hudson.triggers.TimerTrigger>
<spec>H 2 * * *</spec>
</hudson.triggers.TimerTrigger>
</triggers>
<concurrentBuild>false</concurrentBuild>
<builders>
<hudson.tasks.Shell>
<command>
#!/bin/bash set -x #---------To spcify OS wanted to run whole test based on--------- #[naming rule]: #The os name should be consistent with the os name which xcat copycds generated. #Take redhat7.3 for example,the osimage name is rhels7.3-ppc64le-install-compute, #the value of XCAT_TEST_OS should be rhels7.3 export XCAT_TEST_OS=rhels7.4 #---------To spcify target xcat build--------- #If need to test your own build. #comment "XCAT_TEST_BRANCH" line out,move "#" out of below "XCAT_TEST_CORE" line and set corect value #if need to test the latest daily build in build server, #comment "XCAT_TEST_CORE" line out,move "#" out of below "XCAT_TEST_BRANCH" line and set corect value #for example : master or 2.13 export XCAT_TEST_CORE=https://10.2.1.9/install/newbundle_2.13.6sprint1/core-debs-snap.tar.bz2 #---------To spcify target xcat dependency package--------- #If not set, will use the latest dependency package in xcat.org export XCAT_TEST_DEP=http://10.2.1.9/install/httpserver/xcat-dep-201702211334.tar.bz2 #---------To spcify automation framework code repo--------- #For automation development environment, using below 2 line [RECOMMEND] export XCAT_TEST_GIT_REPO=git@github.ibm.com:gongjie/jenkins.git export XCAT_TEST_GIT_BRANCH=devel #---------To specify mailing list --------- #using comma to separate different people export XCAT_TEST_MAILING_LIST=huweihua@cn.ibm.com,bjdengs@cn.ibm.com #---------To specify test case list --------- #If need to customize you own case list, #paste you case in bundle array declare -a bundle=( lsdef_a lsdef_t_o_l lsdef_t_o_l_z INCLUDE:MN_basic.bundle lsdef_t lsdef_t_i_o ) export XCAT_TEST_CASE="${bundle[*]}" #---------To specify the database type---------- #Using Mysql by default export XCAT_TEST_DATABASE=PostgreSQL #---------To specify the additional plugin---------- #using this attribute to specify some customize script which's result will be inserted into normal mail report #The plugin script should be check in Jenkins repo "~/jenkins/plugin" ahead. export XCAT_TEST_PLUGIN=get_p9euhn01_bmc_firmware_version #----------------DO NOT MODIFY BELOW LINES------------- cp /tmp/dengshuai/test.sh . ./test.sh
</command>
</hudson.tasks.Shell>
</builders>
<publishers/>
<buildWrappers/>
<assignedNode>12345</assignedNode>
</project>'''
	#config_xml_name = "config.xml"
	#tree = ET.parse(config_xml_name)###"config.xml"
	#root = tree.getroot()
	root = ET.fromstring(config_string.strip())
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
	return xml
	'''
	config_output_name = "config_output.xml"
	tree.write(config_output_name,xml_declaration=True, encoding='utf-8', method="xml")
'''

def create_job_by_conf(conf_file):
	get_Xml_From_Conf_And_Template_Xml(conf_file)
	#job_name = 'ds_project_test1'#foo_job1
	###xml = resource_string('examples', 'addjob.xml')
	#xml = open('./addjob.xml',encoding='utf8').read()
	#xml = open(config_output_name).read()
	if job_name in jenkins.jobs:
		logger.info('the job named '+job_name+' already exists\n')
	else:
		job = jenkins.create_job(jobname=job_name, xml=xml);

def getDicFromXml(jenkins,projectname):
	#config = jenkins[projectname].get_config()
	#f = open("config_text",'w')
	#f.write(config)
	#f.close()
	bundle_arr=[]
	conf_arr=[]
	conf_dic={}
	conf_dic["project_name"]=projectname
	
	job = jenkins[projectname]
	conf = job.get_config()
	root = ET.fromstring(conf.strip())
	node = root.find('assignedNode')
	if node is None:
		logger.info("assigenedNode is None")
	elif node.text is None:
		logger.info("node.text is None")
	else:
		conf_dic["test_cluster"]=node.text
	
	triggers = root.find('triggers')
	if triggers is None:
		logger.info("triggers is None")
	else:
		timerTrigger = triggers.find('hudson.triggers.TimerTrigger')
		if timerTrigger is None:
			logger.info("build_schedule is None")
		else:
			spec = timerTrigger.find('spec')
			if spec is None:
				logger.info("build_schedule is None")
			elif spec.text is None:
				logger.info("spec.text is None")
			else:
				conf_dic["build_schedule"]=spec.text
	
	builders = root.find('builders')
	if builders is None:
		logger.info('builders is None.\n')
	else:
		shell = builders.find('hudson.tasks.Shell')
		if shell is None:
			logger.info("shell is None.\n")
		else:
			command = shell.find('command')
			if command is None:
				logger.info("command is None.\n")
			elif command.text is None:
				logger.info("command.text is None.\n")
			else:
				command_str = command.text
				commandList = command_str.split("\n")
				for line in commandList:
					line=line.strip()
					index = line.find('#')
					if line == '' or index == 0:
						continue;
					elif index == -1:##the line don't include '#'
						#print('index:',index)
						conf_arr.append(line)
					else:
						line = line[0:index]; line= line.strip(); conf_arr.append(line);
				begin=0
				end=len(conf_arr)-1
				new_len=len(conf_arr)
				#isbundle = 0  ##Record if there is the bundle 
				#isplugin = 0
				for i in range(0,len(conf_arr)):
					if conf_arr[i]=="declare -a bundle=(":
						begin=i
						isbundle=1
					if conf_arr[i]==")":
						end=i
				if isbundle:
					for j in range(begin+1,end):
						bundle_arr.append(conf_arr[j])
				for k in range(0,len(conf_arr)):
					str = conf_arr[k]
					if '=' in str:
						kv_arr = str.split('=')
						str1=kv_arr[0]
						str2=kv_arr[1]
						str1=str1.strip()
						str2=str2.strip()
						if 'XCAT_TEST_OS' in str1:
							conf_dic['os']=str2
						elif 'XCAT_TEST_BRANCH' in str1:
							conf_dic['branch']=str2
						elif 'XCAT_TEST_CORE' in str1:
							conf_dic['customize_xcat_core']=str2
						elif 'XCAT_TEST_DEP' in str1:
							conf_dic['customize_xcat_dep']=str2
						elif 'XCAT_TEST_GIT_BRANCH' in str1:
							if str2=="devel":
								conf_dic['automation_env']="development"
							elif str2=="master":
								conf_dic['automation_env']="production"
						elif 'XCAT_TEST_MAILING_LIST' in str1:
							conf_dic['mailing_list']=str2
						elif 'XCAT_TEST_DATABASE' in str1:
							conf_dic['database']=str2
						elif 'bundle' in str1:
							conf_dic['[customize_bundle]']=bundle_arr
						elif 'XCAT_TEST_PLUGIN' in str1:
							conf_dic['customize_plugin']=str2
	return conf_dic

def get_Config_String_From_Xml(jenkins,projectname):
	conf_dic = getDicFromXml(jenkins,projectname)
	if 'project_name' in conf_dic.keys():
		project_str ='#---------------\nproject_name=' + conf_dic['project_name'] + '\n'
	else:
		project_str = ''
	if 'test_cluster' in conf_dic.keys():
		cluster_str = 'test_cluster=' + conf_dic['test_cluster'] + '\n'
	else:
		cluster_str = ''
	if 'build_schedule' in conf_dic.keys():
		schedule_str = 'build_schedule=' + conf_dic['build_schedule'] + '   #valid value are now or one time, such like 5\n\n'
	else:
		schedule_str = ''
	if 'os' in conf_dic.keys():
		os_str = '#--------------------\nos=' + conf_dic['os'] + '\n'
	else:
		os_str = ''
	if 'branch' in conf_dic.keys():
		branch_str = '#--------------------\nbranch=' + conf_dic['branch'] + '   #valid value are master, 2.13\n'
	else:
		branch_str = ''
	if 'customize_xcat_core' in conf_dic.keys():
		core_str = '#--------------------\ncustomize_xcat_core=' + conf_dic['customize_xcat_core'] + '\n'
	else:
		core_str = ''
	if 'customize_xcat_dep' in conf_dic.keys():
		dep_str = 'customize_xcat_dep=' + conf_dic['customize_xcat_dep'] + '\n\n'
	else:
		dep_str = ''
	if 'automation_env' in conf_dic.keys():
		env_str = '#To choose atuomation environment\nautomation_env=' + conf_dic['automation_env'] + '   #valid value are development,production\n\n'
	else:
		env_str = ''
	if 'mailing_list' in conf_dic.keys():
		mailing_str = '#---------------\nmailing_list=' + conf_dic['mailing_list'] + '\n\n'
	else:
		mailing_str = ''
	if 'database' in conf_dic.keys():
		database_str = '#---------------\ndatabase=' + conf_dic['database'] + '   #valid value are PostgreSQL and MySQL\n\n'
	else:
		database_str = ''
	if '[customize_bundle]' in conf_dic.keys():
		bundle_arr = conf_dic['[customize_bundle]']
		bundle_str='#---------------\n[customize_bundle]\n'
		for one in bundle_arr:
			bundle_str = bundle_str + one + '\n'
	else:
		bundle_str = ''
	if 'customize_plugin' in conf_dic.keys():
		plugin_str = '\n#--------------------\ncustomize_plugin=' + conf_dic['customize_plugin'] + '\n'
	else:
		plugin_str = ''
	conf_str='#this is the config file for a project on Jenkins\n\n%s%s%s%s%s%s%s%s%s%s%s%s' % (project_str,cluster_str,schedule_str,os_str,branch_str,core_str,dep_str,env_str,mailing_str,database_str,bundle_str,plugin_str)
	return conf_str

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


def change_Schedule(jenkins,projectname,timer_str):
	job = None
	if jenkins.has_job(projectname):
		job = jenkins[projectname]
	else:
		logger.error('There is not '+projectname+'in the master.\n')
	conf = job.get_config()
	root = ET.fromstring(conf.strip())
	triggers = root.find('triggers')
	timerTrigger = triggers.find('hudson.triggers.TimerTrigger')
	if timerTrigger is None:
		timerTrigger = ET.SubElement(triggers,'hudson.triggers.TimerTrigger')
	spec = timerTrigger.find('spec')
	spec_arr = timerTrigger.findall('spec')
	#print(len(spec_arr))
	if timer_str=='disable':
		if spec is None:
			spec = ET.SubElement(timerTrigger,'spec')
			spec.text = ''
		elif len(spec_arr)==1:
			spec = ET.SubElement(timerTrigger,'spec')
			spec.text = ''
		elif len(spec_arr)==2:
			spec_tmp = spec_arr[1]
			#print(spec_tmp.text)
			if spec_tmp.text == '' or spec_tmp.text is None:
				pass
			else:
				spec = ET.SubElement(timerTrigger,'spec')
				spec.text = ''
				timerTrigger.remove(spec_arr[0])
		elif len(spec_arr)>2:
			spec_tmp = spec_arr[len(spec_arr)-1]
			if spec_tmp.text == '' or spec_tmp.text is None:
				for i in range(0,len(spec_arr)-2):
					timerTrigger.remove(spec_arr[i])
			else:
				spec = ET.SubElement(timerTrigger,'spec')
				spec.text = ''
				for i in range(0,len(spec_arr)-1):
					timerTrigger.remove(spec_arr[i])
	elif timer_str=='enable':
		if spec is None:
			spec = ET.SubElement(timerTrigger,'spec')
			spec.text = ''
		elif len(spec_arr)==1:
			pass
		elif len(spec_arr)==2:
			spec_tmp = spec_arr[1]
			print(spec_tmp.text)
			if spec_tmp.text == '' or spec_tmp.text is None:
				timerTrigger.remove(spec_tmp)
		elif len(spec_arr)>2:
			spec_tmp = spec_arr[len(spec_arr)-1]
			if spec_tmp.text == '' or spec_tmp.text is None:
				timerTrigger.remove(spec_tmp)
			for i in range(0,len(spec_arr)-2):
				timerTrigger.remove(spec_arr[i])
	else:
		if spec is None:
			spec = ET.SubElement(timerTrigger,'spec')
			spec.text = timer_str
		elif len(spec_arr)==1:
			spec.text = timer_str
		elif len(spec_arr)>1:
			for i in range(0,len(spec_arr)):
				timerTrigger.remove(spec_arr[i])
			spec = ET.SubElement(timerTrigger,'spec')
			spec.text = timer_str
	conf_str = ET.tostring(root).decode('utf-8')
	job.update_config(conf_str)
	#tree1 = ET.ElementTree(root)
	#tree1.write('new1.xml',xml_declaration=True, encoding='utf-8', method="xml")


def get_Schedule(jenkins,projectname):
	job = jenkins[projectname]
	conf = job.get_config()
	root = ET.fromstring(conf.strip())
	triggers = root.find('triggers')
	timerTrigger = triggers.find('hudson.triggers.TimerTrigger')
	if timerTrigger is None:
		return None
	spec = timerTrigger.find('spec')
	if spec is None:
		return None
	return spec.text

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

def get_Assigned_Node(jenkins,projectname):
	job = jenkins[projectname]
	conf = job.get_config()
	root = ET.fromstring(conf.strip())
	node = root.find('assignedNode')
	if node is None:
		return None
	return node.text

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

def get_Command(jenkins,projectname):
	job = jenkins[projectname]
	conf = job.get_config()
	root = ET.fromstring(conf.strip())
	builders = root.find('builders')
	if builders is None:
		return None
	shell = builders.find('hudson.tasks.Shell')
	if shell is None:
		return None
	command = shell.find('command')
	if command is None:
		return None
	return command.text


def change_group_jobs_schedule(jenkins,group_name,timer_str):
	if group_name in jenkins.views:
		for job in jenkins.views[group_name].items():
			print(job[0])
			change_Schedule(jenkins,job[0],timer_str)##job[0]===>the name of job
	else:
		#logger.info('View has been deleted')
		logger.error(group_name+' is not in jenkins.\n')

def usage():
	usage_str='''Usage:
 
To get help:
    $program_name -h

To list existed projects with their group:
    $program_name -m <jenkins_master> -l
 
To modify specific attribute of all project in a group:
    $program_name -m <jenkins_master>  -g  <group_name> [-s <disable| * 5 * * *>]
 
To get configuration of a project
    $program_name -m <jenkins_master>  -p  <project_name>
 
To modify attributes of a project
    $program_name -c <config_file>
 
Options:
    -l: list all group/project information.
    -m: Specify Jenkins’ master.  The vaild values are dev (means automation development environment) or pro (means automation product environment)
    -g: Specify group name in Jenkins master.
    -p: Specify project name in Jenkins master.
    -c: Specify project configuration file.
    -s: Schedule a time when a group starts to run.  The valid values are disable or '* 8 * * *' '''
	print(usage_str)

def print_groupList(jenkins):
	for group_name in jenkins.views.keys():
		if group_name != 'all':
			print('>'+group_name)
			for job in jenkins.views[group_name].items():
				print('  ->'+job[0])

def main(argv):
	master = ''
	group = ''
	jenkins=None
	is_s = False
	is_p = False
	is_g = False
	try:
		opts, args = getopt.getopt(argv,"hm:lg:s:p:c:",["help","master=","list","group=","schedule=","project=","configuration="])
	except getopt.GetoptError:
		#print 'the parameter list is not found, or when the required parameter is null.'
		usage()
		sys.exit(2)
	for opt, arg in opts:
		if opt in ("-s", "--schedule"):
			is_s = True
		if opt in ("-p","--project"):
			is_p = True
		if opt in ("-g","--group"):
			is_g = True
	for opt, arg in opts:
		#if opt == '-h':
		if opt in ("-h","--help"):
			usage()
			sys.exit()
		elif opt in ("-m", "--master"):
			master = arg
			jenkins_url = 'http://'+master+':8080' #'http://10.2.4.25:8080'
			jenkins =  Jenkins(jenkins_url,username="dengshuai_super",password="8080")
			'''
			if master == '10.2.4.25':
				jenkins_url = 'http://10.2.4.25:8080'
				jenkins =  Jenkins(jenkins_url,username="admin",password="cluster")
			elif master == '10.4.32.1':
				jenkins_url = 'http://10.4.32.1:8080'
				jenkins = Jenkins(jenkins_url,username="admin",password="cluster")
			'''
		elif opt in ("-l","--list"):
			print_groupList(jenkins)
			sys.exit()
		elif opt in ("-g","--group"):
			group = arg
		elif opt in ("-p","--project"):
			project_name = arg
		elif opt in ("-p","--project") and is_s==False:
			project_name = arg
			##To get configuration of a project
			conf_str=get_Config_String_From_Xml(jenkins,project_name)
			print(conf_str)
			sys.exit()
		elif (opt in ("-s", "--schedule") and is_g):
			timer = arg
			change_group_jobs_schedule(jenkins,group,timer)
			sys.exit()
		elif (opt in ("-s", "--schedule") and is_p):
			timer = arg
			change_Schedule(jenkins,project_name,timer)
			sys.exit()


if __name__ == '__main__':

	main(sys.argv[1:])
	
	

'''
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
