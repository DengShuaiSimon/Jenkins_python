from __future__ import print_function
###from pkg_resources import resource_string
from jenkinsapi.jenkins import Jenkins
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger()


jenkins_url = "http://localhost:8080/"
###jenkins_url = "http://dengshuai_super:8080@127.0.0.1:8080"
jenkins = Jenkins('http://localhost:8080')
#jenkins = Jenkins(jenkins_url,username="dengshuai_super",password="8080")
job_name = 'test6'#foo_job1

###xml = resource_string('examples', 'addjob.xml')

xml = open('./addjob.xml',encoding='utf8').read()


print(xml)

job = jenkins.create_job(jobname=job_name, xml=xml)

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
test_view_name = 'SimpleListView1'
my_view = jenkins.views.create(test_view_name)
my_view.add_job(job_name, my_job)

#assert len(my_view) == 1   ##len(my_view) can get the number of jobs in the view

#logger.info('Attempting to delete view that already exists')
#del jenkins.views[test_view_name]

#if test_view_name in jenkins.views:
#    logger.error('View was not deleted')
#else:
#    logger.info('View has been deleted')
