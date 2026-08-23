import Quickshell
import Niri
import QtQuick
import QtQuick.Layouts

RowLayout {
  Layout.fillWidth: false
  spacing: 4 * Config.paddingScale

  Niri {
    id: niri
    Component.onCompleted: connect()
    onErrorOccurred: function(error) { console.error("Niri error:", error) }
  }

  Component.onCompleted: niri.workspaces.maxCount = Config.maxWorkspaces

  Repeater {
    model: niri.workspaces

    delegate: Rectangle {
      id: wsButton
      required property var model
      property bool isActive: model.isFocused
      property string activeBg: "#4d5258"
      property string inactiveBg: "#393c41"

      Layout.preferredWidth: 17.5 * Config.pillScale
      Layout.preferredHeight: Layout.preferredWidth
      radius: 8 * Config.pillScale
      color: isActive ? activeBg : inactiveBg

      Behavior on color { ColorAnimation { duration: 120 } }

      Text {
        anchors.centerIn: parent
        text: wsButton.model.index
        color: wsButton.isActive ? "#ffffff" : "#dae0ea"
        font {
          family: Theme.fontFamily
          pixelSize: 9 * Config.pillScale
          weight: 300
        }
      }

      MouseArea {
        anchors.fill: parent
        onClicked: niri.focusWorkspaceById(wsButton.model.id)
        cursorShape: Qt.PointingHandCursor
      }
    }
  }
}
