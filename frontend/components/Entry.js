import React, {Component} from "react";
import ReactDOM from "react-dom";
import App from "./App";
import {Button} from "react-bootstrap"

export default class Entry extends Component{
  constructor(props){
    super(props);
    this.state = {
      login: '',
      password: '',
      enter: false,
    }

    this.submit = this.submit.bind(this);

  }

  submit(){
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
	            console.log(data);
	            });
	        })
    }
  }

  render(){
    let entryWindow =

    <div class="login-page" id="entry">
      <div class="form">
          <div class="greetings">Добро пожаловать</div>
          <form class="login-form">
            <input type="text" placeholder="Логин" onChange={(e) => this.setState({login: e.target.value})}/>
            <input type="password" placeholder="Пароль" onChange={(e) => this.setState({password: e.target.value})}/>
            <Button onClick={this.submit}>Войти</Button>
          </form>
      </div>
    </div>

    ;

    return(entryWindow)
  }
}
