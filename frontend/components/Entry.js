import React, {Component} from "react";
import ReactDOM from "react-dom";
import App from "./App";
import {Button, Alert, Row, Col} from "react-bootstrap"

export default class Entry extends Component{
  constructor(props){
    super(props);
    this.state = {
      login: '',
      password: '',
      enter: false,
      token: null,
      user_status: "Guest",
      error: false,
      alert: false,
      description: "Неправильно указан логин или пароль"
    }

    this.submit = this.submit.bind(this);
    this.exit = this.exit.bind(this);

  }

  exit(){
    this.setState({
      token: null,
      user_status: "Guest",
      enter: false,
    })
  }
  
  submit(){
    const main = this;
    let data = {login: this.state.login, password: this.state.password}
    if(data.login && data.password){
      fetch('/Entry',
	        {
	          method: 'post',
	          headers: {
	            'Content-Type':'application/json',
	            "Access-Control-Allow-Origin": "*",
	            "Access-Control-Allow-Headers": "Origin, X-Requested-With, Content-Type, Accept"
	          },
	          body: JSON.stringify(data),
	        })
	        .then(
	        function(response) {
	          if (response.status !== 200) {
	            console.log('Looks like there was a problem. Status Code: ' + response.status);
	            if(response.status === 500){
	                console.log("Status: 500")
	            }
	            return;
	          }

	          // Examine the text in the response
	          response.json()
	          .then(function(data) {
              if(data != null){
                main.setState({
                  enter: true,
                  token: data.token,
                  user_status: data.status,
                })
                console.log("Welcome")
              }
              else{
                console.log("Not right");
                main.setState({alert: true});
              }
	            });
	        }).catch(function (error) {
  			    console.log('error: ', error)
  					main.setState({error: true})
  			  })
    }
  }

  render(){
    let user = {
      user_status: this.state.user_status,
      token: this.state.token,
    }
    const main = this;

    let entryWindow = (!this.state.enter) ?

    <div class="login-page" id="entry">
      <div class="form">
            <div class="greetings">Добро пожаловать</div>
            <form class="login-form" id="but">
              <input type="text" placeholder="Логин" onChange={(e) => this.setState({login: e.target.value})}
                                                      onKeyPress={ event => {
                                                        if(event.key == 'Enter' ){
                                                          main.submit();
                                                        }
                                                        return false;
                                                      }}
                />
              <input type="password" placeholder="Пароль" onChange={(e) => this.setState({password: e.target.value})}
                                                          onKeyPress={ event => {
                                                            if(event.key == 'Enter' ){
                                                              main.submit();
                                                            }
                                                            return false;
                                                          }}
                />
              <Button onClick={this.submit}>Войти</Button>
            </form>
          {
            (this.state.alert) ?
            <Alert variant="danger" className="mt-3 paw" onClose={() => this.setState({alert: false})} dismissible>
              <p>
                {this.state.description}
              </p>
            </Alert>
            :
            null
          }
      </div>
    </div>

    : <App exit={this.exit} user={user}/>;

    return(entryWindow)
  }
}
