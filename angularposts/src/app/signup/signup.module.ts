import { NgModule } from '@angular/core';
import { CommonModule } from '@angular/common';
import { ReactiveFormsModule } from '@angular/forms';
import { SignupComponent } from './signup.component';
import { SignupRoutingModule } from './signup-routing.module';


@NgModule({
  declarations: [
    SignupComponent,
  ],
  imports: [
    SignupRoutingModule,
    CommonModule,
    ReactiveFormsModule
  ],
  providers: [],
})
export class SignupModule { }
