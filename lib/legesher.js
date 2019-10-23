"use babel";

import LegesherView from "./legesher-view";
import { CompositeDisposable } from "atom";

export default {
    legesherView: null,
    modalPanel: null,
    subscriptions: null,

    activate(state) {
        this.legesherView = new LegesherView(state.legesherViewState);
        this.modalPanel = atom.workspace.addModalPanel({ item: this.legesherView.getElement(), visible: false });

        // Events subscribed to in atom's system can be easily cleaned up with a CompositeDisposable
        this.subscriptions = new CompositeDisposable();

        // Register command that toggles this view
        this.subscriptions.add(atom.commands.add("atom-workspace", {
            "legesher:toggle": () => this.toggleLanguage()
        }));

        // Register command that opens settings
        this.subscriptions.add(atom.commands.add("atom-workspace", {
            "legesher:open-settings": () => this.openSettings()
        }));
    },

    deactivate() {
        this.modalPanel.destroy();
        this.subscriptions.dispose();
        this.legesherView.destroy();
    },

    serialize() {
        return { legesherViewState: this.legesherView.serialize() };
    },

    toggleLanguage() {
        console.log("Legesher was toggled!");

        if (this.modalPanel.isVisible()) {
            this.modalPanel.hide();
        } else {
            const editor = atom.workspace.getActiveTextEditor();
            // const grammar = editor.getGrammar();
            // console.log('CURRRENT GRAMMAR',grammar)
            const words = editor.getText().split(/\s+/).length;
            this.legesherView.setCount(words);
            this.modalPanel.show();
        }
    },

    openSettings() {
        console.log("Settings were opened.");
        return this.modalPanel.isVisible() ?
            this.modalPanel.hide() :
            this.modalPanel.show();
    }
};