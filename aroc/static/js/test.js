liftControls = {
  name: "LiftControls",
  props: {
      className: {
          type: String,
          default: ""
      },
      id: {
          type: String,
          default: ""
      }
  },
  data: function() {
      return {
          model: window.GlobalUtil.model,
          isDown: !1,
          isLoop: !1,
          interval: 0,
          isOver: !1
      };
  },
  methods: {
      onDown: function(event) {
          this.isDown = true;
      },
      onUp: function(event) {
          this.isDown = false;
      }

  }
}
, liftPanel = {
  name: "LiftPanel",
  components: {
      LiftControls: liftControls
  },
  data: function() {
      return {
          speed:25,
          absoluteValue: 0, 
          isABSActive: false,
          isReseting:false,
          isReferenceActive: false,
          isReferencing: false, 
          isEditingAbsoluteValue: false,
          actualPosition: 0,
          isWebSocketConnected: false,
          isMotorActive: false,

          // -------- Для сглаживания: --------
          oldPosition: 0,
          newPosition: 0,
          lastUpdateTime: 0,  // когда получили реальные данные
          
          updateModelTimer: null
      };
  },
  methods: {
      updateAnimationTick() {
          let interpolatedPosition = this.actualPosition;
          this.$store.state.liftPosition = interpolatedPosition;
          window.CommandsRobotSocket.model.commonStatusMgr.updateModelFlag = 2;
        },

      startUpdateModelFlagTimer() {
          if (this.updateModelTimer) return;
          this.updateModelTimer = setInterval(() => {
          if (this.isMotorActive) {
              this.updateAnimationTick();
          }
          }, 100);
      },
  
      stopUpdateModelFlagTimer() {
          if (this.updateModelTimer) {
          clearInterval(this.updateModelTimer);
          this.updateModelTimer = null;
          }
      },
          

      pollMotorData() {
          const state = window.igusController.getState();

          this.actualPosition = state.position;
          this.isReferenceActive = state.homing;
          this.isErrorStateActive = state.errorState;
          this.isWebSocketConnected = state.connected;       
          this.updateActualPosition();
          this.updateAnimationTick();
        },
    
        // ---------------------
        //  ОСНОВНЫЕ ОПЕРАЦИИ
        // ---------------------

      async updateActualPosition() {
          if (!this.isEditingAbsoluteValue) {
              this.absoluteValue = this.actualPosition / 1000;
              this.lastUpdateTime = Date.now(); 
            }
      },
      onDown: function(event) {
          var t = this;
          if (this.isDown == false){
          }
          this.isDown = true;
          this.onDownId = event.target.id;
          this.targetId = event.target.id;
      
          this.interval = setInterval(function() {
              if (t.isDown) {
                  let speed = window.CommandsRobotSocket.model.robot.state.remote.speedPercent*10000;
                  window.motorCtrl.sendCommand({
                      command: event.target.id,
                      params: {
                          position: 0,
                          velocity: speed,
                          acc: speed,
                          wait: true
                      }
                      });
              } else {
                  window.motorCtrl.sendCommand({
                      command: "shutdown",
                      params: {
                          position: 0,
                          velocity: speed,
                          acc: speed,
                          wait: true
                      }
                      });
                  clearInterval(t.interval);
                  t.onDownId = "";
              }
          }, 200); 
      
          return false;
      },
      onUp: function(event) {
          if (this.isDown == true){    
              event.preventDefault(); // Останавливаем стандартное поведение
              this.isOver = false;    // Можем использовать, если требуется дополнительная логика для 'mouseover' событий
              clearInterval(this.interval); // Очищаем интервал, который посылает команды в процессе удержания
              window.motorCtrl.sendCommand({
                  command: "shutdown",
                  params: {
                      position: 0,
                      velocity: speed,
                      acc: speed,
                      wait: true
                  }
                  });
              this.onDownId = ""; // Сбрасываем идентификатор кнопки
              this.isDown = false;}    // Устанавливаем флаг на false, чтобы прекратить отправку команд
      },
      
      handleGo: async function() {
          this.isEditingAbsoluteValue = false;
          
          this.isABSActive = true;
          this.newPosition = this.absoluteValue * 1000;
          if (this.newPosition < 0 || this.newPosition > 115000) {
              alert("Value is not in range 0-115 cm.");
              this.isABSActive = false;
              return;
          }

          this.speed = window.CommandsRobotSocket.model.robot.state.remote.speedPercent * 10000;
          try {
              this.isMotorActive = true;
              
              await window.igusController.moveToPosition(this.newPosition,  this.speed,  this.speed);
          } catch (error) {
              console.error("ABS error:", error);
          } finally {
              this.isABSActive = false;
              this.isMotorActive = false;
          }
      },

      handleReference: async function() {
          this.isReferencing = true;
          try {
              this.isMotorActive = true;
              await window.igusController.homing();
          } catch (error) {
              console.error("Reference error:", error);
          } finally {
              this.isReferencing = false;
              this.isMotorActive = false;
          }
      },
      startEditingAbsoluteValue() {
          // Когда пользователь вошёл в поле ввода (focus)
          this.isEditingAbsoluteValue = true;
        },
      stopEditingAbsoluteValue() {
          // Когда пользователь вышел из поля ввода (blur)
          this.isEditingAbsoluteValue = true;
          // Можно сразу «привести» значение к нужному формату,
          // либо отправить серверу, либо обновить мотор, если нужно.
        },
      handleReset: async function() {
          this.isReseting = true;
          try {
              await window.igusController.sendCommand({ command: "fault_reset" });
              await window.igusController.sendCommand({ command: "shutdown" });
          } catch (error) {
              console.error("Reset error:", error);
          } finally {
              this.isReseting = false;
          }

      }
  },
  created() {

      this.pollTimer = setInterval(() => {
        this.pollMotorData();
      }, 500); // например, каждые 300 мс
    },
    beforeDestroy() {
      if (this.pollTimer) {
        clearInterval(this.pollTimer);
      }
    },

  computed: {
      ABSButtonText() {
          return this.isABSActive ? 'Moving...' : 'Start';
      },
      referenceButtonText() {
          if (this.isReferencing) {
              return 'Referencing...';
          } else if (this.isReferenceActive) {
              return 'Referenced';
          } else {
              return 'Reference';
          }
      }
  },
  watch: {
      isMotorActive(newVal) {
        if (newVal) {
          // Если мотор активируется – запускаем таймер
          this.startUpdateModelFlagTimer();
        } else {
          // Если мотор перестал быть активным – останавливаем таймер
          this.stopUpdateModelFlagTimer();
        }
      }
    },
  render(h) {
      let dataVAttr = { "data-v-3c7ad43f":"" }; // Атрибут для всех эл
      const rootClass = [
          "lift-panel",
          "font-vw-20",
          "uf-font-medium",
          "row-fr-2",
         
        ];
      return h("div", {class: rootClass, attrs: dataVAttr}, [
          h("div", { class: "panels col-fr-2", attrs: dataVAttr }, [
              // Left Panel c условием блокировки
              h("div", {
                  class: [
                      "left-panel",
                      { "disabled-panel": !this.isWebSocketConnected || this.isMotorActive }
                  ],
                  attrs: dataVAttr
              }, [
                  h("div", { class: "button-group", attrs: dataVAttr }, [
                      h("button", {
                          class: "button",
                          attrs: { ...dataVAttr, id: "lift-z-increase" },
                          on: {
                              touchstart: this.onDown,
                              mousedown: this.onDown,
                              touchend: this.onUp,
                              mouseup: this.onUp,
                              mouseout: this.onUp
                          }
                      }, "Up"),
  
                      h("button", {
                          class: "button",
                          attrs: { ...dataVAttr, id: "lift-z-decrease" },
                          on: {
                              touchstart: this.onDown,
                              mousedown: this.onDown,
                              touchend: this.onUp,
                              mouseup: this.onUp,
                              mouseout: this.onUp
                          }
                      }, "Down")
                  ]),
  
                  h("div", { class: "input-group", attrs: dataVAttr }, [
                      h("div", { class: "input-wrapper", attrs: dataVAttr }, [
                        h("input", {
                          attrs: {
                            ...dataVAttr,
                            id: "absolute-input",
                            type: "number",
                            class: "input",
                            min: "0",
                            max: "200",
                            placeholder: "Enter height (0-200)"
                          },
                          domProps: {
                            value: this.absoluteValue
                          },
                          on: {
                            focus: () => {
                              // Когда пользователь «заходит» в инпут
                              this.isEditingAbsoluteValue = true;
                            },
                            blur: () => {
                              // Когда пользователь «уходит» из инпута
                              this.isEditingAbsoluteValue = true;
                              // Можно сразу тут проверить/исправить/отправить значение,
                              // смотря какая логика вам нужна.
                            },
                            input: (event) => {
                              // Пока пользователь печатает, сохраняем ввод в this.absoluteValue
                              this.absoluteValue = event.target.value;
                            }
                          }
                        }),
                        h("span", { class: "unit", attrs: dataVAttr }, "cm")
                      ]),
                    
                      h("button", {
                        class: "abs-button",
                        style: {
                          backgroundColor: this.isABSActive ? "white" : "#3662EC",
                          color: this.isABSActive ? "black" : "white"
                        },
                        attrs: {
                          ...dataVAttr,
                          disabled: this.isABSActive
                        },
                        on: { click: this.handleGo }
                      }, this.ABSButtonText)
                    ])                          
              ]),
  
              // Right Panel
              h("div", { class: "right-panel right-panel", attrs: dataVAttr }, [
                  h("div", { class: "button-group", attrs: dataVAttr }, [
                      h("button", {
                          class: "reference-button",
                          style: {
                              backgroundColor: this.isReferenceActive ? '#24b01c' : '#3662EC',
                              color: this.isReferencing ? 'black' : 'white',
                              backgroundColor: this.isReferencing ? 'white' : (this.isReferenceActive ? '#24b01c' : '#3662EC')
                          },
                          attrs: {
                              ...dataVAttr,
                              disabled: this.isReferencing ? true : false  // Добавляем атрибут disabled, если кнопка белая
                          },
                          on: { click: this.handleReference }
                      }, this.referenceButtonText),
  
                      h("button", {
                          class: "reset-button",
                          attrs: dataVAttr,
                          on: { click: this.handleReset }
                      }, "Fault Reset")
                  ])
              ])
          ])
      ]);
  }
  
}   