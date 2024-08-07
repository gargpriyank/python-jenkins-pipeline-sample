pipeline {
    agent {
        label any
    }

    stages {
        stage('Retrieve data via REST API and update ini file') {
            steps {
                script {
                    sh "${PYTHON36}/bin/pip3.6 install --target ${env.WORKSPACE}/python-scripts requests"

                    def yamlConfigFileData
                    try {
                        yamlConfigFileData = readYaml file: "${env.WORKSPACE}/jenkins-config/config.yaml"
                    } catch (IOException ioe) {
                        echo "config.yaml file is corrupted."
                    }

                    def iniConfigFiles
                    try {
                        iniConfigFiles = findFiles(glob: "**/*.ini", excludes: "**/jenkins-config/**,**/python-scripts/**,Jenkinsfile,*.*")
                    } catch (IOException ioe) {
                        echo "There is no ini config file in the parent folder to process."
                        sh "exit 1"
                    }

                    def gitPath = "${yamlConfigFileData.git_url}".replaceAll(/https?:\/\//, '')
                    def jsonReviewers = []

                    for (iniConfigFile in iniConfigFiles) {
                        dir('python-scripts') {
                            withCredentials([usernamePassword(credentialsId: 'rest-api-creds', passwordVariable: 'restAPIPwd', usernameVariable: 'restAPIUser')]) {
                                sh "${PYTHON36}/bin/python3.6 rest_data_retrieval_ini_config_update.py --ini_config_file ${env.WORKSPACE}/${iniConfigFile.path} -url ${yamlConfigFileData.rest_api_url} -user ${restAPIUser} -pwd ${restAPIPwd}"
                            }

                            sh "git add ${env.WORKSPACE}/${iniConfigFile.path}"
                        }
                    }

                    dir('python-scripts') {
                        withCredentials([usernamePassword(credentialsId: "${yamlConfigFileData.git_creds-id}", passwordVariable: 'gitCredPwd', usernameVariable: 'gitCredUsr')]) {
                            jsonReviewers = sh(script: "${PYTHON36}/bin/python3.6 git_service.py -url ${yamlConfigFileData.git_api_default_reviewer_url} -user ${gitCredUsr} -pwd ${gitCredPwd} -project ${yamlConfigFileData.git_project} -repo ${yamlConfigFileData.git_repo}", returnStdout: true)
                        }
                    }

                    def currentTimestamp = new Date().format("yyyyMMddHHmmss")
                    def createPullReqJSONObj = readJSON file: "${env.WORKSPACE}/jenkins-config/create_pull_request.json"
                    createPullReqJSONObj.fromRef.id = "" + "refs/heads/ini-config-${currentTimestamp}" + ""
                    createPullReqJSONObj.fromRef.repository.slug = "" + "${yamlConfigFileData.git_repo}" + ""
                    createPullReqJSONObj.fromRef.repository.project.key = "" + "${yamlConfigFileData.git_project}" + ""
                    createPullReqJSONObj.toRef.id = "" + "refs/heads/${yamlConfigFileData.git_branch_merge_to}" + ""
                    createPullReqJSONObj.toRef.repository.slug = "" + "${yamlConfigFileData.git_repo}" + ""
                    createPullReqJSONObj.toRef.repository.project.key = "" + "${yamlConfigFileData.git_project}" + ""
                    jsonReviewersObj = readJSON text: jsonReviewers
                    createPullReqJSONObj.reviewers = jsonReviewersObj
                    writeJSON file: "${env.WORKSPACE}/jenkins-config/create_pull_request.json", json: createPullReqJSONObj, pretty: 2

                    withCredentials([usernamePassword(credentialsId: "${yamlConfigFileData.git_creds-id}", passwordVariable: 'gitCredPwd', usernameVariable: 'gitCredUsr')]) {
                        sh """
                                git config --local user.name "${yamlConfigFileData.git_user_name}"
                                git config --local user.email "${yamlConfigFileData.git_user_email}"
                                git commit -m "Updating ini config files with network details" || true
                                git branch ini-config-${currentTimestamp}
                                git push https://${gitCredUsr}:${gitCredPwd}@${gitPath} ini-config-${currentTimestamp}
                                curl -L -X POST --user ${gitCredUsr}:${gitCredPwd} --header 'Content-Type: application/json' ${yamlConfigFileData.git_api_url}/projects/${configFileData.git_project}/repos/${configFileData.git_repo}/pull-requests --data @${env.WORKSPACE}/jenkins-config/create_pull_request.json
                            """
                    }
                }
            }
        }
    }

    post('Clean up Workspace') {
        always {
            cleanWs()
        }
    }
}