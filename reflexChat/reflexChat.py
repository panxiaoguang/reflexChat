"""Welcome to Reflex! This file outlines the steps to create a basic app."""


import reflex as rx
import json
import aiohttp
import os


class ChatState(rx.State):
    """The app state."""
    chat_history: list[tuple[str, str]]
    _messages = [{"role": "system", "content": "You are a smart and versatile artificial intelligence assistant. You will faithfully follow the user's instructions to solve and answer questions. Your answers are detailed and professional, and they do not contain offensive information."}]
    question: str
    model: str = "qwen/qwen1.5-14b-chat-awq"
    Generation: bool = False

    @rx.background
    async def get_answer(self):
        async with aiohttp.ClientSession() as session:
            answer = ""
            async with self:
                self._messages.append(
                    {"role": "user", "content": self.question})
                self.chat_history.append((self.question, answer))
                self.question = ""
            # Construct the post request to the API.
            async with session.post(
                f"https://gateway.ai.cloudflare.com/v1/{os.environ['ID']}/workers-ai/workers-ai/@cf/{self.model}",
                headers={"Authorization": f"Bearer {os.environ['API_TOKEN']}"},
                json={
                    "messages": self.get_value(self._messages),
                    "stream": True,
                    "max_tokens": 2048
                }
            ) as response:
                # Check if the response status is OK.
                if response.status == 200:
                    # Asynchronously process each line in the streaming response.
                    async for line in response.content:
                        async with self:
                            if not self.Generation:
                                return
                        decoded_line = line.decode('utf-8').strip()
                        if decoded_line.startswith('data: '):
                            json_data = decoded_line[len('data: '):]
                            # Handle the JSON data.
                            if decoded_line == 'data: [DONE]':
                                async with self:
                                    self.Generation = not self.Generation
                                    self._messages.append(
                                        {"role": "assistant", "content": answer})
                                    return
                            else:
                                data = json.loads(json_data)
                                answer += data.get('response')
                                async with self:
                                    self.chat_history[-1] = (
                                        self.chat_history[-1][0], answer)
                                    # push the final response to the role of system
                else:
                    async with self:
                        self.chat_history[-1] = (self.chat_history[-1][0],
                                                 f"Failed to fetch data: {response.status}")

    def clear_answer(self):
        self.chat_history = []
        self._messages = [{"role": "system", "content": "You are a smart and versatile artificial intelligence assistant. You will faithfully follow the user's instructions to solve and answer questions. Your answers are detailed and professional, and they do not contain offensive information."}]

    def toggle_running(self):
        self.Generation = not self.Generation
        if self.Generation:
            return ChatState.get_answer()


def navebar() -> rx.Component:
    model_list = ["meta/llama-2-7b-chat-fp16",
                  "meta/llama-2-7b-chat-int8",
                  "mistral/mistral-7b-instruct-v0.1",
                  "thebloke/deepseek-coder-6.7b-base-awq",
                  "thebloke/deepseek-coder-6.7b-instruct-awq",
                  "deepseek-ai/deepseek-math-7b-base",
                  "deepseek-ai/deepseek-math-7b-instruct",
                  "thebloke/discolm-german-7b-v1-awq",
                  "tiiuae/falcon-7b-instruct",
                  "google/gemma-2b-it-lora",
                  "google/gemma-7b-it",
                  "google/gemma-7b-it-lora",
                  "nousresearch/hermes-2-pro-mistral-7b",
                  "thebloke/llama-2-13b-chat-awq",
                  "meta-llama/llama-2-7b-chat-hf-lora",
                  "thebloke/llamaguard-7b-awq",
                  "thebloke/mistral-7b-instruct-v0.1-awq",
                  "mistralai/mistral-7b-instruct-v0.2",
                  "mistral/mistral-7b-instruct-v0.2-lora",
                  "thebloke/neural-chat-7b-v3-1-awq",
                  "openchat/openchat-3.5-0106",
                  "thebloke/openhermes-2.5-mistral-7b-awq",
                  "microsoft/phi-2",
                  "qwen/qwen1.5-0.5b-chat",
                  "qwen/qwen1.5-1.8b-chat",
                  "qwen/qwen1.5-14b-chat-awq",
                  "qwen/qwen1.5-7b-chat-awq",
                  "defog/sqlcoder-7b-2",
                  "nexusflow/starling-lm-7b-beta",
                  "tinyllama/tinyllama-1.1b-chat-v1.0",
                  "thebloke/zephyr-7b-beta-awq"]
    """The app navbar."""
    return rx.flex(
        rx.flex(
            rx.image(src="logo.png", width="90px"),
            width='40%',
        ),
        rx.flex(
            rx.select(
                model_list,
                default_value="qwen/qwen1.5-14b-chat-awq",
                radius="large",
                width="30%",
                on_change=ChatState.set_model,
            ),
            width="60%",
        ),
        width='100%',
        class_name="p-4 border-b sticky"
    )


def qa(question: str, answer: str) -> rx.Component:
    component_style = {
        "h1": lambda text: rx.heading(
            text, size="5", margin_y="1em"
        ),
        "h2": lambda text: rx.heading(
            text, size="3", margin_y="1em"
        ),
        "h3": lambda text: rx.heading(
            text, size="1", margin_y="1em"
        ),
        "p": lambda text: rx.text(
            text, margin_y="1em"
        ),
        "code": lambda text: rx.code(text, color="orange", weight="bold"),
        "codeblock": lambda text, **props: rx.code_block(
            text, **props, theme="light", margin_y="1em", wrap_long_lines=True,
        ),
        "a": lambda text, **props: rx.link(
            text, **props, color="blue", _hover={"color": "orange"}
        ),
    }
    return rx.box(
        rx.box(
            rx.heading("You:", size="3", class_name="mt-1 font-semibold"),
            rx.markdown(question, component_map=component_style),
        ),
        rx.box(
            rx.heading("Bot:", size="3", class_name="mt-1 font-semibold"),
            rx.markdown(answer, component_map=component_style),
        ),
    )


def chat() -> rx.Component:
    return rx.scroll_area(
        rx.center(
            rx.box(
                rx.foreach(
                    ChatState.chat_history,
                    lambda messages: qa(messages[0], messages[1]),
                ),
                width='60%',
            ),
        ),
        class_name="mt-14",
        type='hover',
        height='64vh',
    )


def action_bar() -> rx.Component:
    return rx.flex(
        rx.text_area(
            placeholder="Ask a question",
            value=ChatState.question,
            on_change=ChatState.set_question,
            width="600px",
            auto_height=True,
        ),
        rx.button(
            rx.cond(
                ~ChatState.Generation,
                "Generate",
                "Stop"
            ),
            height="4.5em",
            width="6.5em",
            variant="soft",
            radius="medium",
            _hover={"cursor": "pointer"},
            on_click=ChatState.toggle_running,
        ),
        rx.button(
            "New Chat",
            height="4.5em",
            width="6.5em",
            class_name="text-2xl",
            radius="medium",
            on_click=ChatState.clear_answer,
            _hover={"cursor": "pointer"},
            color_scheme="iris",
        ),
        spacing="1",
        justify="center",
        width="100%",
        class_name="pt-4"
    )


def footer() -> rx.Component:
    return rx.center(
        rx.text("Based on ",
                rx.link("Reflex", href="https://reflex.dev/"),
                " and ",
                rx.link("Cloudflare workers AI",
                        href="https://dash.cloudflare.com/"),
                ". Click ",
                rx.link(
                    "here", href="https://developers.cloudflare.com/workers-ai/models/#text-generation"),
                " to know the models."),
    )


def index() -> rx.Component:
    return rx.flex(
        navebar(),
        chat(),
        action_bar(),
        footer(),
        direction="column",
    )


app = rx.App()
app.add_page(index)
