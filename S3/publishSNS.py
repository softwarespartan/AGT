import boto.sns;
import logging;

logging.basicConfig(filename="sns-topic.log", level=logging.DEBUG)

connection = boto.sns.SNSConnection()

topicname = "test_topic"

topicarn = connection.create_topic(topicname)

print topicname, "has been successfully created with a topic ARN of", topicarn

print connection.DefaultRegionEndpoint
print connection.DefaultRegionName