"""PRE-EXISTING: copied verbatim from github.com/jenniferevangelista-de/night-guard
(guard/signals.py at commit 7a30a2f, MIT), before this hackathon.

Risk signals Night Guard looks for, and the fixed texts shown to the child and to the family.

All texts are fixed (not generated) so the tone stays clear and nothing wrong is improvised.

kid:     what the child sees. Short, says "danger" plainly, and compares it to a real-world
         situation kids already know (a stranger on the street), the modern version of the
         old "don't go off without telling us" warnings. Never blames the child.
parent:  why it matters, for the family alert.
lesson:  the longer explanation used in Practice and when the child taps "why?".

Signals are based on documented tactics: Public Safety Canada (2025, gaming grooming tactics,
multiple accounts after blocking), NCMEC (2026, financial sextortion), Thorn (2022, 2025).
"""

SIGNALS = {
    "secrecy": {
        "label": {"en": "Asked to keep a secret", "pt": "Pediu segredo"},
        "kid": {
            "en": "DANGER: someone asked you to hide this from your family. It's like a stranger on the street saying \"come with me, but don't tell your mom\". You don't go, and you tell an adult.",
            "pt": "PERIGO: alguém pediu pra você esconder isso da sua família. É como um estranho na rua dizendo \"vem comigo, mas não conta pra sua mãe\". A gente não vai, e conta pra um adulto.",
        },
        "parent": {
            "en": "Asking a child to hide a conversation from family is a well-documented warning sign of grooming.",
            "pt": "Pedir para a criança esconder a conversa da família é um sinal de alerta bem documentado de aliciamento.",
        },
        "lesson": {
            "en": "Asking you to keep a secret from your family is a big red flag. Safe friends don't need secrets.",
            "pt": "Pedir para esconder algo da sua família é um grande sinal de alerta. Amigos de verdade não precisam de segredo.",
        },
        "weight": 3,
    },
    "platform_move": {
        "label": {"en": "Wants to move to another app", "pt": "Quer mudar de aplicativo"},
        "kid": {
            "en": "Careful: they want to take you to another app. It's like someone saying \"let's leave the playground and go somewhere nobody can see\". Stay where you are.",
            "pt": "Cuidado: querem te levar pra outro app. É como alguém dizendo \"vamos sair do parquinho e ir pra um lugar onde ninguém vê\". Fica onde você está.",
        },
        "parent": {
            "en": "Moving a child to a private or encrypted app is a key step: it takes the chat away from the platform's safety tools (NCMEC reports this happening faster each year).",
            "pt": "Levar a criança para um app privado ou criptografado é um passo-chave: tira a conversa das ferramentas de segurança da plataforma (o NCMEC relata que isso acontece cada vez mais rápido).",
        },
        "lesson": {
            "en": "Moving the chat to a private app (WhatsApp, Snap, Discord DM) takes you away from places with safety tools.",
            "pt": "Levar a conversa para um app privado (WhatsApp, Snap, DM do Discord) tira você de onde existem ferramentas de proteção.",
        },
        "weight": 2,
    },
    "personal_info": {
        "label": {"en": "Asked for personal info", "pt": "Pediu dados pessoais"},
        "kid": {
            "en": "Careful: they asked where you live or study. You wouldn't tell your address to a stranger on the bus. Online is the same.",
            "pt": "Cuidado: perguntaram onde você mora ou estuda. Você não falaria seu endereço pra um estranho no ônibus. Na internet é igual.",
        },
        "parent": {
            "en": "Real name, school or neighborhood lets a stranger find the child offline.",
            "pt": "Nome completo, escola ou bairro permitem que um estranho encontre a criança fora da internet.",
        },
        "lesson": {
            "en": "Your real name, school, address or phone stay offline. A game friend doesn't need them.",
            "pt": "Nome completo, escola, endereço e telefone ficam fora do jogo. Um amigo do jogo não precisa disso.",
        },
        "weight": 2,
    },
    "age_probe": {
        "label": {"en": "Asked your age or if you're alone", "pt": "Perguntou idade ou se está sozinho"},
        "kid": {
            "en": "Heads up: they asked your age or if you're alone. A stranger knocking and asking \"are your parents home?\" doesn't get an answer.",
            "pt": "Atenção: perguntaram sua idade ou se você está sozinho. Estranho que bate na porta perguntando \"seus pais estão em casa?\" não ganha resposta.",
        },
        "parent": {
            "en": "Questions about age or being alone help someone decide how to approach a child.",
            "pt": "Perguntas sobre idade ou se está sozinho ajudam alguém a decidir como se aproximar da criança.",
        },
        "lesson": {
            "en": "Questions like 'how old are you?' or 'are your parents home?' help strangers figure out how to approach you.",
            "pt": "Perguntas como 'quantos anos você tem?' ou 'seus pais estão em casa?' ajudam estranhos a saber como chegar em você.",
        },
        "weight": 1,
    },
    "photo_request": {
        "label": {"en": "Asked for a photo or video", "pt": "Pediu foto ou vídeo"},
        "kid": {
            "en": "DANGER: they asked for a photo or video of you. Never send it. A photo that leaves your phone can't come back. Tell an adult now.",
            "pt": "PERIGO: pediram foto ou vídeo seu. Nunca mande. Foto que sai do seu celular não volta mais. Conta pra um adulto agora.",
        },
        "parent": {
            "en": "A photo request can be how sextortion starts: images can later be used to threaten the child or demand money (NCMEC received 50,000+ financial sextortion reports in 2025).",
            "pt": "Um pedido de foto pode ser o começo da sextorsão: depois a imagem pode ser usada para ameaçar a criança ou cobrar dinheiro (o NCMEC recebeu mais de 50 mil denúncias de sextorsão financeira em 2025).",
        },
        "lesson": {
            "en": "Never send photos or videos of yourself to someone you met online. Saying no is always OK.",
            "pt": "Nunca mande foto ou vídeo seu para alguém que conheceu online. Dizer não é sempre ok.",
        },
        "weight": 3,
    },
    "gift_offer": {
        "label": {"en": "Offered gifts or free stuff", "pt": "Ofereceu presente ou coisa grátis"},
        "kid": {
            "en": "Careful: free Robux or skins from a stranger is like candy from a stranger. It can be a trick.",
            "pt": "Cuidado: Robux ou skin grátis de estranho é como doce de estranho. Pode ser uma pegadinha.",
        },
        "parent": {
            "en": "In-game gifts are a documented way to build trust and create a feeling of debt.",
            "pt": "Presentes no jogo são uma forma documentada de ganhar confiança e criar sensação de dívida.",
        },
        "lesson": {
            "en": "Free Robux, skins or gems from a stranger can come with a catch. Real gifts don't need anything back.",
            "pt": "Robux, skins ou gemas grátis de um estranho podem ter uma pegadinha. Presente de verdade não pede nada em troca.",
        },
        "weight": 2,
    },
    "credential_request": {
        "label": {"en": "Asked for a password or code", "pt": "Pediu senha ou código"},
        "kid": {
            "en": "DANGER: they asked for your password or a code. That's like giving a stranger the key to your house. Nobody needs it, not even \"staff\".",
            "pt": "PERIGO: pediram sua senha ou um código. Isso é como dar a chave da sua casa pra um estranho. Ninguém precisa, nem \"moderador\".",
        },
        "parent": {
            "en": "Password or code requests are used to steal accounts; a stolen account can be used to contact the child's friends.",
            "pt": "Pedido de senha ou código serve para roubar a conta; uma conta roubada pode ser usada para falar com os amigos da criança.",
        },
        "lesson": {
            "en": "Nobody needs your password or login code. Not friends, not 'staff', not anyone.",
            "pt": "Ninguém precisa da sua senha ou código de login. Nem amigo, nem 'moderador', ninguém.",
        },
        "weight": 3,
    },
    "suspicious_link": {
        "label": {"en": "Sent a suspicious link", "pt": "Mandou um link suspeito"},
        "kid": {
            "en": "Careful: this link promises free stuff. It's like a door with a prize sign that's actually a trap. Don't click. Ask an adult.",
            "pt": "Cuidado: esse link promete coisa grátis. É como uma porta com placa de prêmio que na verdade é armadilha. Não clica. Pergunta pra um adulto.",
        },
        "parent": {
            "en": "\"Free currency\" links are a known way to steal game accounts and personal data.",
            "pt": "Links de \"moeda grátis\" são um jeito conhecido de roubar contas de jogo e dados pessoais.",
        },
        "lesson": {
            "en": "Links promising free stuff can steal accounts. Use \"Check it without opening\" and ask a trusted adult before opening it.",
            "pt": "Links prometendo coisas grátis podem roubar contas. Use \"Conferir sem abrir\" e peça ajuda a um adulto antes de abrir.",
        },
        "weight": 2,
    },
    "meet_offline": {
        "label": {"en": "Wants to meet in person", "pt": "Quer encontrar pessoalmente"},
        "kid": {
            "en": "DANGER: they want to meet you in person. You never go out to meet someone from the internet without telling your family, just like you never leave home without telling them.",
            "pt": "PERIGO: querem te encontrar pessoalmente. Você nunca sai pra encontrar alguém da internet sem avisar sua família, igual você nunca sai de casa sem avisar.",
        },
        "parent": {
            "en": "A request to meet offline is the highest-risk step. Act today.",
            "pt": "Pedido de encontro presencial é o passo de maior risco. Aja hoje.",
        },
        "lesson": {
            "en": "Meeting someone from the internet is never something to plan alone. Tell a trusted adult right away.",
            "pt": "Encontrar alguém da internet nunca é algo para combinar sozinho. Conte para um adulto de confiança agora.",
        },
        "weight": 3,
    },
    "pressure": {
        "label": {"en": "Pressure, guilt or threats", "pt": "Pressão, culpa ou ameaça"},
        "kid": {
            "en": "Careful: they're pushing you. Real friends accept a \"no\". If someone gets angry or threatens you, that's a sign to stop and tell an adult.",
            "pt": "Cuidado: estão te pressionando. Amigo de verdade aceita um \"não\". Se alguém fica bravo ou ameaça, é sinal pra parar e contar pra um adulto.",
        },
        "parent": {
            "en": "Guilt, urgency and threats are used to push a child past their own limits.",
            "pt": "Culpa, pressa e ameaças são usadas para empurrar a criança além dos próprios limites.",
        },
        "lesson": {
            "en": "'If you were my friend you would...' or threats are pressure tricks. You did nothing wrong by saying no.",
            "pt": "'Se você fosse meu amigo faria...' ou ameaças são truques de pressão. Você não fez nada errado em dizer não.",
        },
        "weight": 2,
    },
    "isolation": {
        "label": {"en": "Tries to turn you against family/friends", "pt": "Tenta te afastar de família/amigos"},
        "kid": {
            "en": "Careful: they say only they understand you. Someone who wants to pull you away from your family is not on your side.",
            "pt": "Cuidado: dizem que só eles te entendem. Quem quer te afastar da sua família não está do seu lado.",
        },
        "parent": {
            "en": "Isolating the child from family and friends makes them easier to control and less likely to ask for help.",
            "pt": "Afastar a criança da família e dos amigos deixa ela mais fácil de controlar e menos propensa a pedir ajuda.",
        },
        "lesson": {
            "en": "'Only I understand you' or 'your parents wouldn't get it' is a trick to isolate you.",
            "pt": "'Só eu te entendo' ou 'seus pais não iam entender' é um truque para te isolar.",
        },
        "weight": 2,
    },
    "flattery": {
        "label": {"en": "Says you're 'mature for your age'", "pt": "Diz que você é 'maduro pra idade'"},
        "kid": {
            "en": "Heads up: \"you're so mature for your age\" is a classic trick to make you feel special and trust them fast.",
            "pt": "Atenção: \"você é muito maduro pra sua idade\" é um truque clássico pra você se sentir especial e confiar rápido.",
        },
        "parent": {
            "en": "Flattery about being mature is a documented trust-building tactic (Public Safety Canada, 2025).",
            "pt": "Elogiar a criança como \"madura\" é uma tática documentada para ganhar confiança (Public Safety Canada, 2025).",
        },
        "lesson": {
            "en": "Compliments like 'you're more mature than kids your age' are used to make you feel special and trust someone fast.",
            "pt": "Elogios como 'você é mais maduro que a galera da sua idade' são usados pra você se sentir especial e confiar rápido.",
        },
        "weight": 1,
    },
    "returning_after_block": {
        "label": {"en": "Came back with a new account", "pt": "Voltou com outra conta"},
        "kid": {
            "en": "DANGER: someone you blocked came back with a new account. If someone keeps coming back after a \"no\", tell an adult.",
            "pt": "PERIGO: alguém que você bloqueou voltou com outra conta. Se alguém insiste depois de um \"não\", conta pra um adulto.",
        },
        "parent": {
            "en": "Creating new accounts to re-contact a child after being blocked is a documented tactic (Public Safety Canada, 2025).",
            "pt": "Criar contas novas para voltar a falar com a criança depois de bloqueado é uma tática documentada (Public Safety Canada, 2025).",
        },
        "lesson": {
            "en": "If someone makes a new account to talk to you after you blocked them, they are not respecting your 'no'.",
            "pt": "Se alguém cria outra conta pra falar com você depois de bloqueado, ele não está respeitando o seu 'não'.",
        },
        "weight": 3,
    },
    "sextortion": {
        "label": {"en": "Threat to share images or demand money", "pt": "Ameaça espalhar imagem ou cobra dinheiro"},
        "kid": {
            "en": "DANGER: this is blackmail. You are NOT in trouble. Don't pay and don't send anything else. Tell an adult right now, they can help.",
            "pt": "PERIGO: isso é chantagem. Você NÃO está encrencado. Não pague e não mande mais nada. Conta pra um adulto agora, eles podem ajudar.",
        },
        "parent": {
            "en": "This is sextortion: threats to share images or demands for money or gift cards. It is a crime. Stay calm with your child, don't pay, keep the evidence, report it.",
            "pt": "Isto é sextorsão: ameaça de espalhar imagens ou cobrança de dinheiro ou gift card. É crime. Fique calmo com a criança, não pague, guarde as provas, denuncie.",
        },
        "lesson": {
            "en": "If someone threatens to share pictures or asks for money, it's blackmail and it's a crime. You're not in trouble, tell an adult right away.",
            "pt": "Se alguém ameaça espalhar fotos ou pede dinheiro, é chantagem e é crime. Você não está encrencado, conta pra um adulto na hora.",
        },
        "weight": 3,
    },
}

SIGNAL_IDS = list(SIGNALS.keys())

# Signals that, alone, are serious enough to tell the family (per default family rules).
HIGH_ALONE = {"photo_request", "meet_offline", "credential_request", "returning_after_block", "sextortion"}

# What the family should do, by severity. Shown under every family alert.
PARENT_STEPS = {
    "high": {
        "en": ["Talk with your child today, calmly and without punishment: kids who get in trouble stop telling.",
               "Don't delete anything: take screenshots of the chat and the contact's profile.",
               "Block and report the account inside the app.",
               "If there are image requests, threats or money demands: report it (SaferNet Brasil: new.safernet.org.br/denuncie, or NCMEC CyberTipline: report.cybertip.org) and contact the police. Don't pay."],
        "pt": ["Converse com a criança hoje, com calma e sem castigo: criança que leva bronca para de contar.",
               "Não apague nada: tire print da conversa e do perfil do contato.",
               "Bloqueie e denuncie a conta dentro do app.",
               "Se houver pedido de imagem, ameaça ou cobrança: denuncie (SaferNet: new.safernet.org.br/denuncie) e procure a polícia. Não pague."],
    },
    "medium": {
        "en": ["Ask your child about it in a calm moment, without judgment.",
               "Check who the contact is and whether your child knows them offline.",
               "Review the app's privacy settings together."],
        "pt": ["Pergunte para a criança sobre isso num momento calmo, sem julgamento.",
               "Veja quem é o contato e se a criança conhece a pessoa fora da internet.",
               "Revisem juntos as configurações de privacidade do app."],
    },
    "low": {
        "en": ["Nothing urgent. Mention it naturally in your next conversation about online friends."],
        "pt": ["Nada urgente. Comente com naturalidade na próxima conversa sobre amigos da internet."],
    },
}
