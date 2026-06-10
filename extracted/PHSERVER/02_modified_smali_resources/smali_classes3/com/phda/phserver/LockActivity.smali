.class public Lcom/phda/phserver/LockActivity;
.super Landroid/app/Activity;
.source "LockActivity.java"


# static fields
.field private static final COLOR_BG:I = -0xefe7e0

.field private static final COLOR_GRAY:I = -0x4f413b

.field private static final COLOR_GREEN:I = -0xc600ec

.field private static final COLOR_HINT:I = -0x9f8275

.field private static final COLOR_NEON:I = -0xef10

.field private static final COLOR_RED:I = -0xadae

.field private static final COLOR_WHITE:I = -0x1

.field private static final LOCKOUT_DELAY_MS:I = 0x7d0

.field private static final MAX_ATTEMPTS:I = 0x5

.field private static final PASSWORD_SHA256:Ljava/lang/String; = "456d12e33d0edb0eec5aee0bd933b654e0ccfb16506adbc588af712ba654dcc3"


# instance fields
.field private attempts:I

.field private input:Landroid/widget/EditText;

.field private status:Landroid/widget/TextView;

.field private submitBtn:Landroid/widget/Button;


# direct methods
.method public constructor <init>()V
    .registers 2

    .line 34
    invoke-direct {p0}, Landroid/app/Activity;-><init>()V

    .line 46
    const/4 v0, 0x0

    iput v0, p0, Lcom/phda/phserver/LockActivity;->attempts:I

    return-void
.end method

.method static synthetic access$000(Lcom/phda/phserver/LockActivity;)V
    .registers 1

    .line 34
    invoke-direct {p0}, Lcom/phda/phserver/LockActivity;->onSubmit()V

    return-void
.end method

.method static synthetic access$100(Lcom/phda/phserver/LockActivity;)Landroid/widget/TextView;
    .registers 1

    .line 34
    iget-object p0, p0, Lcom/phda/phserver/LockActivity;->status:Landroid/widget/TextView;

    return-object p0
.end method

.method private autoStartServerInBackground()V
    .registers 4

    .line 276
    invoke-virtual {p0}, Lcom/phda/phserver/LockActivity;->getApplication()Landroid/app/Application;

    move-result-object v0

    .line 277
    if-nez v0, :cond_7

    return-void

    .line 278
    :cond_7
    new-instance v1, Ljava/lang/Thread;

    new-instance v2, Lcom/phda/phserver/LockActivity$6;

    invoke-direct {v2, p0, v0}, Lcom/phda/phserver/LockActivity$6;-><init>(Lcom/phda/phserver/LockActivity;Landroid/app/Application;)V

    const-string v0, "PHSERVER-AutoStart"

    invoke-direct {v1, v2, v0}, Ljava/lang/Thread;-><init>(Ljava/lang/Runnable;Ljava/lang/String;)V

    .line 331
    const/4 v0, 0x1

    invoke-virtual {v1, v0}, Ljava/lang/Thread;->setDaemon(Z)V

    .line 332
    :try_start_17
    invoke-virtual {v1}, Ljava/lang/Thread;->start()V
    :try_end_1a
    .catchall {:try_start_17 .. :try_end_1a} :catchall_1b

    goto :goto_1c

    :catchall_1b
    move-exception v0

    .line 333
    :goto_1c
    return-void
.end method

.method private static marginTop(Landroid/widget/LinearLayout$LayoutParams;I)Landroid/widget/LinearLayout$LayoutParams;
    .registers 2

    .line 192
    iput p1, p0, Landroid/widget/LinearLayout$LayoutParams;->topMargin:I

    .line 193
    return-object p0
.end method

.method private mp()Landroid/widget/LinearLayout$LayoutParams;
    .registers 4

    .line 186
    new-instance v0, Landroid/widget/LinearLayout$LayoutParams;

    const/4 v1, -0x1

    const/4 v2, -0x2

    invoke-direct {v0, v1, v2}, Landroid/widget/LinearLayout$LayoutParams;-><init>(II)V

    return-object v0
.end method

.method private onSubmit()V
    .registers 5

    .line 197
    iget-object v0, p0, Lcom/phda/phserver/LockActivity;->input:Landroid/widget/EditText;

    invoke-virtual {v0}, Landroid/widget/EditText;->getText()Landroid/text/Editable;

    move-result-object v0

    const-string v1, ""

    if-nez v0, :cond_c

    move-object v0, v1

    goto :goto_16

    :cond_c
    iget-object v0, p0, Lcom/phda/phserver/LockActivity;->input:Landroid/widget/EditText;

    invoke-virtual {v0}, Landroid/widget/EditText;->getText()Landroid/text/Editable;

    move-result-object v0

    invoke-virtual {v0}, Ljava/lang/Object;->toString()Ljava/lang/String;

    move-result-object v0

    .line 198
    :goto_16
    invoke-static {v0}, Lcom/phda/phserver/LockActivity;->sha256Hex(Ljava/lang/String;)Ljava/lang/String;

    move-result-object v0

    .line 199
    const-string v2, "456d12e33d0edb0eec5aee0bd933b654e0ccfb16506adbc588af712ba654dcc3"

    invoke-virtual {v2, v0}, Ljava/lang/String;->equalsIgnoreCase(Ljava/lang/String;)Z

    move-result v0

    if-eqz v0, :cond_45

    .line 200
    iget-object v0, p0, Lcom/phda/phserver/LockActivity;->status:Landroid/widget/TextView;

    const v1, -0xc600ec

    invoke-virtual {v0, v1}, Landroid/widget/TextView;->setTextColor(I)V

    .line 201
    iget-object v0, p0, Lcom/phda/phserver/LockActivity;->status:Landroid/widget/TextView;

    const-string v1, "Senha correta. Abrindo PHSERVER..."

    invoke-virtual {v0, v1}, Landroid/widget/TextView;->setText(Ljava/lang/CharSequence;)V

    .line 202
    new-instance v0, Landroid/os/Handler;

    invoke-static {}, Landroid/os/Looper;->getMainLooper()Landroid/os/Looper;

    move-result-object v1

    invoke-direct {v0, v1}, Landroid/os/Handler;-><init>(Landroid/os/Looper;)V

    new-instance v1, Lcom/phda/phserver/LockActivity$4;

    invoke-direct {v1, p0}, Lcom/phda/phserver/LockActivity$4;-><init>(Lcom/phda/phserver/LockActivity;)V

    const-wide/16 v2, 0xfa

    invoke-virtual {v0, v1, v2, v3}, Landroid/os/Handler;->postDelayed(Ljava/lang/Runnable;J)Z

    .line 219
    return-void

    .line 221
    :cond_45
    iget v0, p0, Lcom/phda/phserver/LockActivity;->attempts:I

    add-int/lit8 v0, v0, 0x1

    iput v0, p0, Lcom/phda/phserver/LockActivity;->attempts:I

    .line 222
    iget-object v0, p0, Lcom/phda/phserver/LockActivity;->input:Landroid/widget/EditText;

    invoke-virtual {v0, v1}, Landroid/widget/EditText;->setText(Ljava/lang/CharSequence;)V

    .line 223
    iget v0, p0, Lcom/phda/phserver/LockActivity;->attempts:I

    const v1, -0xadae

    const/4 v2, 0x5

    if-lt v0, v2, :cond_83

    .line 224
    iget-object v0, p0, Lcom/phda/phserver/LockActivity;->status:Landroid/widget/TextView;

    invoke-virtual {v0, v1}, Landroid/widget/TextView;->setTextColor(I)V

    .line 225
    iget-object v0, p0, Lcom/phda/phserver/LockActivity;->status:Landroid/widget/TextView;

    const-string v1, "Muitas tentativas erradas. Encerrando..."

    invoke-virtual {v0, v1}, Landroid/widget/TextView;->setText(Ljava/lang/CharSequence;)V

    .line 226
    iget-object v0, p0, Lcom/phda/phserver/LockActivity;->submitBtn:Landroid/widget/Button;

    const/4 v1, 0x0

    invoke-virtual {v0, v1}, Landroid/widget/Button;->setEnabled(Z)V

    .line 227
    iget-object v0, p0, Lcom/phda/phserver/LockActivity;->input:Landroid/widget/EditText;

    invoke-virtual {v0, v1}, Landroid/widget/EditText;->setEnabled(Z)V

    .line 228
    new-instance v0, Landroid/os/Handler;

    invoke-static {}, Landroid/os/Looper;->getMainLooper()Landroid/os/Looper;

    move-result-object v1

    invoke-direct {v0, v1}, Landroid/os/Handler;-><init>(Landroid/os/Looper;)V

    new-instance v1, Lcom/phda/phserver/LockActivity$5;

    invoke-direct {v1, p0}, Lcom/phda/phserver/LockActivity$5;-><init>(Lcom/phda/phserver/LockActivity;)V

    const-wide/16 v2, 0x7d0

    invoke-virtual {v0, v1, v2, v3}, Landroid/os/Handler;->postDelayed(Ljava/lang/Runnable;J)Z

    goto :goto_a3

    .line 238
    :cond_83
    iget v0, p0, Lcom/phda/phserver/LockActivity;->attempts:I

    sub-int/2addr v2, v0

    .line 239
    iget-object v0, p0, Lcom/phda/phserver/LockActivity;->status:Landroid/widget/TextView;

    invoke-virtual {v0, v1}, Landroid/widget/TextView;->setTextColor(I)V

    .line 240
    iget-object v0, p0, Lcom/phda/phserver/LockActivity;->status:Landroid/widget/TextView;

    new-instance v1, Ljava/lang/StringBuilder;

    invoke-direct {v1}, Ljava/lang/StringBuilder;-><init>()V

    const-string v3, "Senha incorreta. Tentativas restantes: "

    invoke-virtual {v1, v3}, Ljava/lang/StringBuilder;->append(Ljava/lang/String;)Ljava/lang/StringBuilder;

    move-result-object v1

    invoke-virtual {v1, v2}, Ljava/lang/StringBuilder;->append(I)Ljava/lang/StringBuilder;

    move-result-object v1

    invoke-virtual {v1}, Ljava/lang/StringBuilder;->toString()Ljava/lang/String;

    move-result-object v1

    invoke-virtual {v0, v1}, Landroid/widget/TextView;->setText(Ljava/lang/CharSequence;)V

    .line 242
    :goto_a3
    return-void
.end method

.method private static sha256Hex(Ljava/lang/String;)Ljava/lang/String;
    .registers 6

    .line 246
    :try_start_0
    const-string v0, "SHA-256"

    invoke-static {v0}, Ljava/security/MessageDigest;->getInstance(Ljava/lang/String;)Ljava/security/MessageDigest;

    move-result-object v0

    .line 247
    const-string v1, "UTF-8"

    invoke-virtual {p0, v1}, Ljava/lang/String;->getBytes(Ljava/lang/String;)[B

    move-result-object p0

    invoke-virtual {v0, p0}, Ljava/security/MessageDigest;->digest([B)[B

    move-result-object p0

    .line 248
    new-instance v0, Ljava/lang/StringBuilder;

    array-length v1, p0

    mul-int/lit8 v1, v1, 0x2

    invoke-direct {v0, v1}, Ljava/lang/StringBuilder;-><init>(I)V

    .line 249
    array-length v1, p0

    const/4 v2, 0x0

    :goto_1a
    if-ge v2, v1, :cond_33

    aget-byte v3, p0, v2

    .line 250
    and-int/lit16 v3, v3, 0xff

    .line 251
    const/16 v4, 0x10

    if-ge v3, v4, :cond_29

    const/16 v4, 0x30

    invoke-virtual {v0, v4}, Ljava/lang/StringBuilder;->append(C)Ljava/lang/StringBuilder;

    .line 252
    :cond_29
    invoke-static {v3}, Ljava/lang/Integer;->toHexString(I)Ljava/lang/String;

    move-result-object v3

    invoke-virtual {v0, v3}, Ljava/lang/StringBuilder;->append(Ljava/lang/String;)Ljava/lang/StringBuilder;

    .line 249
    add-int/lit8 v2, v2, 0x1

    goto :goto_1a

    .line 254
    :cond_33
    invoke-virtual {v0}, Ljava/lang/StringBuilder;->toString()Ljava/lang/String;

    move-result-object p0
    :try_end_37
    .catch Ljava/lang/Exception; {:try_start_0 .. :try_end_37} :catch_38

    return-object p0

    .line 255
    :catch_38
    move-exception p0

    .line 256
    const-string p0, ""

    return-object p0
.end method


# virtual methods
.method protected onCreate(Landroid/os/Bundle;)V
    .registers 13

    .line 58
    invoke-super {p0, p1}, Landroid/app/Activity;->onCreate(Landroid/os/Bundle;)V

    .line 59
    const-string p1, "PHSERVER"

    invoke-virtual {p0, p1}, Lcom/phda/phserver/LockActivity;->setTitle(Ljava/lang/CharSequence;)V

    .line 63
    invoke-direct {p0}, Lcom/phda/phserver/LockActivity;->autoStartServerInBackground()V

    invoke-virtual {p0}, Lcom/phda/phserver/LockActivity;->getApplicationContext()Landroid/content/Context;

    move-result-object v0

    invoke-static {v0}, Lcom/phda/phserver/AutoProvision;->onAppStart(Landroid/content/Context;)V

    .line 65
    nop

    .line 66
    invoke-virtual {p0}, Lcom/phda/phserver/LockActivity;->getResources()Landroid/content/res/Resources;

    move-result-object v0

    invoke-virtual {v0}, Landroid/content/res/Resources;->getDisplayMetrics()Landroid/util/DisplayMetrics;

    move-result-object v0

    .line 65
    const/4 v1, 0x1

    const/high16 v2, 0x3f800000    # 1.0f

    invoke-static {v1, v2, v0}, Landroid/util/TypedValue;->applyDimension(IFLandroid/util/DisplayMetrics;)F

    move-result v0

    float-to-int v0, v0

    .line 68
    new-instance v2, Landroid/widget/LinearLayout;

    invoke-direct {v2, p0}, Landroid/widget/LinearLayout;-><init>(Landroid/content/Context;)V

    .line 69
    invoke-virtual {v2, v1}, Landroid/widget/LinearLayout;->setOrientation(I)V

    .line 70
    invoke-virtual {v2, v1}, Landroid/widget/LinearLayout;->setGravity(I)V

    .line 71
    const v3, -0xefe7e0

    invoke-virtual {v2, v3}, Landroid/widget/LinearLayout;->setBackgroundColor(I)V

    .line 72
    mul-int/lit8 v3, v0, 0x20

    mul-int/lit8 v4, v0, 0x40

    invoke-virtual {v2, v3, v4, v3, v3}, Landroid/widget/LinearLayout;->setPadding(IIII)V

    .line 74
    new-instance v4, Landroid/widget/TextView;

    invoke-direct {v4, p0}, Landroid/widget/TextView;-><init>(Landroid/content/Context;)V

    .line 75
    invoke-virtual {v4, p1}, Landroid/widget/TextView;->setText(Ljava/lang/CharSequence;)V

    .line 76
    const/4 p1, -0x1

    invoke-virtual {v4, p1}, Landroid/widget/TextView;->setTextColor(I)V

    .line 77
    const/high16 v5, 0x42100000    # 36.0f

    const/4 v6, 0x2

    invoke-virtual {v4, v6, v5}, Landroid/widget/TextView;->setTextSize(IF)V

    .line 78
    const/16 v5, 0x11

    invoke-virtual {v4, v5}, Landroid/widget/TextView;->setGravity(I)V

    .line 79
    invoke-direct {p0}, Lcom/phda/phserver/LockActivity;->mp()Landroid/widget/LinearLayout$LayoutParams;

    move-result-object v7

    invoke-virtual {v2, v4, v7}, Landroid/widget/LinearLayout;->addView(Landroid/view/View;Landroid/view/ViewGroup$LayoutParams;)V

    .line 81
    new-instance v4, Landroid/widget/TextView;

    invoke-direct {v4, p0}, Landroid/widget/TextView;-><init>(Landroid/content/Context;)V

    .line 82
    const-string v7, "Servidor MySQL para Android"

    invoke-virtual {v4, v7}, Landroid/widget/TextView;->setText(Ljava/lang/CharSequence;)V

    .line 83
    const v7, -0xef10

    invoke-virtual {v4, v7}, Landroid/widget/TextView;->setTextColor(I)V

    .line 84
    const/high16 v8, 0x41400000    # 12.0f

    invoke-virtual {v4, v6, v8}, Landroid/widget/TextView;->setTextSize(IF)V

    .line 85
    invoke-virtual {v4, v5}, Landroid/widget/TextView;->setGravity(I)V

    .line 86
    invoke-direct {p0}, Lcom/phda/phserver/LockActivity;->mp()Landroid/widget/LinearLayout$LayoutParams;

    move-result-object v9

    mul-int/lit8 v10, v0, 0x4

    invoke-static {v9, v10}, Lcom/phda/phserver/LockActivity;->marginTop(Landroid/widget/LinearLayout$LayoutParams;I)Landroid/widget/LinearLayout$LayoutParams;

    move-result-object v9

    invoke-virtual {v2, v4, v9}, Landroid/widget/LinearLayout;->addView(Landroid/view/View;Landroid/view/ViewGroup$LayoutParams;)V

    .line 88
    new-instance v4, Landroid/widget/TextView;

    invoke-direct {v4, p0}, Landroid/widget/TextView;-><init>(Landroid/content/Context;)V

    .line 89
    const-string v9, "Acesso protegido"

    invoke-virtual {v4, v9}, Landroid/widget/TextView;->setText(Ljava/lang/CharSequence;)V

    .line 90
    const v9, -0x4f413b

    invoke-virtual {v4, v9}, Landroid/widget/TextView;->setTextColor(I)V

    .line 91
    const/high16 v10, 0x41600000    # 14.0f

    invoke-virtual {v4, v6, v10}, Landroid/widget/TextView;->setTextSize(IF)V

    .line 92
    invoke-virtual {v4, v5}, Landroid/widget/TextView;->setGravity(I)V

    .line 93
    invoke-direct {p0}, Lcom/phda/phserver/LockActivity;->mp()Landroid/widget/LinearLayout$LayoutParams;

    move-result-object v10

    invoke-static {v10, v3}, Lcom/phda/phserver/LockActivity;->marginTop(Landroid/widget/LinearLayout$LayoutParams;I)Landroid/widget/LinearLayout$LayoutParams;

    move-result-object v10

    invoke-virtual {v2, v4, v10}, Landroid/widget/LinearLayout;->addView(Landroid/view/View;Landroid/view/ViewGroup$LayoutParams;)V

    .line 95
    new-instance v4, Landroid/widget/TextView;

    invoke-direct {v4, p0}, Landroid/widget/TextView;-><init>(Landroid/content/Context;)V

    .line 96
    const-string v10, "Digite a senha de acesso"

    invoke-virtual {v4, v10}, Landroid/widget/TextView;->setText(Ljava/lang/CharSequence;)V

    .line 97
    invoke-virtual {v4, v9}, Landroid/widget/TextView;->setTextColor(I)V

    .line 98
    invoke-virtual {v4, v6, v8}, Landroid/widget/TextView;->setTextSize(IF)V

    .line 99
    invoke-direct {p0}, Lcom/phda/phserver/LockActivity;->mp()Landroid/widget/LinearLayout$LayoutParams;

    move-result-object v8

    mul-int/lit8 v9, v0, 0x18

    invoke-static {v8, v9}, Lcom/phda/phserver/LockActivity;->marginTop(Landroid/widget/LinearLayout$LayoutParams;I)Landroid/widget/LinearLayout$LayoutParams;

    move-result-object v8

    invoke-virtual {v2, v4, v8}, Landroid/widget/LinearLayout;->addView(Landroid/view/View;Landroid/view/ViewGroup$LayoutParams;)V

    .line 101
    new-instance v4, Landroid/widget/EditText;

    invoke-direct {v4, p0}, Landroid/widget/EditText;-><init>(Landroid/content/Context;)V

    iput-object v4, p0, Lcom/phda/phserver/LockActivity;->input:Landroid/widget/EditText;

    .line 102
    iget-object v4, p0, Lcom/phda/phserver/LockActivity;->input:Landroid/widget/EditText;

    const/16 v8, 0x12

    invoke-virtual {v4, v8}, Landroid/widget/EditText;->setInputType(I)V

    .line 104
    iget-object v4, p0, Lcom/phda/phserver/LockActivity;->input:Landroid/widget/EditText;

    invoke-virtual {v4, p1}, Landroid/widget/EditText;->setTextColor(I)V

    .line 105
    iget-object v4, p0, Lcom/phda/phserver/LockActivity;->input:Landroid/widget/EditText;

    const v8, -0x9f8275

    invoke-virtual {v4, v8}, Landroid/widget/EditText;->setHintTextColor(I)V

    .line 106
    iget-object v4, p0, Lcom/phda/phserver/LockActivity;->input:Landroid/widget/EditText;

    const-string v10, "****"

    invoke-virtual {v4, v10}, Landroid/widget/EditText;->setHint(Ljava/lang/CharSequence;)V

    .line 107
    iget-object v4, p0, Lcom/phda/phserver/LockActivity;->input:Landroid/widget/EditText;

    invoke-virtual {v4, v1}, Landroid/widget/EditText;->setSingleLine(Z)V

    .line 108
    iget-object v1, p0, Lcom/phda/phserver/LockActivity;->input:Landroid/widget/EditText;

    const/high16 v4, 0x41b00000    # 22.0f

    invoke-virtual {v1, v6, v4}, Landroid/widget/EditText;->setTextSize(IF)V

    .line 109
    iget-object v1, p0, Lcom/phda/phserver/LockActivity;->input:Landroid/widget/EditText;

    invoke-virtual {v1, v5}, Landroid/widget/EditText;->setGravity(I)V

    .line 110
    iget-object v1, p0, Lcom/phda/phserver/LockActivity;->input:Landroid/widget/EditText;

    const/4 v4, 0x6

    invoke-virtual {v1, v4}, Landroid/widget/EditText;->setImeOptions(I)V

    .line 111
    iget-object v1, p0, Lcom/phda/phserver/LockActivity;->input:Landroid/widget/EditText;

    new-instance v4, Lcom/phda/phserver/LockActivity$1;

    invoke-direct {v4, p0}, Lcom/phda/phserver/LockActivity$1;-><init>(Lcom/phda/phserver/LockActivity;)V

    invoke-virtual {v1, v4}, Landroid/widget/EditText;->setOnEditorActionListener(Landroid/widget/TextView$OnEditorActionListener;)V

    .line 122
    iget-object v1, p0, Lcom/phda/phserver/LockActivity;->input:Landroid/widget/EditText;

    invoke-direct {p0}, Lcom/phda/phserver/LockActivity;->mp()Landroid/widget/LinearLayout$LayoutParams;

    move-result-object v4

    mul-int/lit8 v10, v0, 0x8

    invoke-static {v4, v10}, Lcom/phda/phserver/LockActivity;->marginTop(Landroid/widget/LinearLayout$LayoutParams;I)Landroid/widget/LinearLayout$LayoutParams;

    move-result-object v4

    invoke-virtual {v2, v1, v4}, Landroid/widget/LinearLayout;->addView(Landroid/view/View;Landroid/view/ViewGroup$LayoutParams;)V

    .line 124
    new-instance v1, Landroid/widget/Button;

    invoke-direct {v1, p0}, Landroid/widget/Button;-><init>(Landroid/content/Context;)V

    iput-object v1, p0, Lcom/phda/phserver/LockActivity;->submitBtn:Landroid/widget/Button;

    .line 125
    iget-object v1, p0, Lcom/phda/phserver/LockActivity;->submitBtn:Landroid/widget/Button;

    const-string v4, "ENTRAR"

    invoke-virtual {v1, v4}, Landroid/widget/Button;->setText(Ljava/lang/CharSequence;)V

    .line 126
    iget-object v1, p0, Lcom/phda/phserver/LockActivity;->submitBtn:Landroid/widget/Button;

    const/4 v4, 0x0

    invoke-virtual {v1, v4}, Landroid/widget/Button;->setAllCaps(Z)V

    .line 127
    iget-object v1, p0, Lcom/phda/phserver/LockActivity;->submitBtn:Landroid/widget/Button;

    invoke-virtual {v1, p1}, Landroid/widget/Button;->setTextColor(I)V

    .line 128
    new-instance p1, Landroid/graphics/drawable/GradientDrawable;

    invoke-direct {p1}, Landroid/graphics/drawable/GradientDrawable;-><init>()V

    .line 129
    invoke-virtual {p1, v7}, Landroid/graphics/drawable/GradientDrawable;->setColor(I)V

    .line 130
    int-to-float v1, v10

    invoke-virtual {p1, v1}, Landroid/graphics/drawable/GradientDrawable;->setCornerRadius(F)V

    .line 131
    nop

    .line 132
    iget-object v10, p0, Lcom/phda/phserver/LockActivity;->submitBtn:Landroid/widget/Button;

    invoke-virtual {v10, p1}, Landroid/widget/Button;->setBackground(Landroid/graphics/drawable/Drawable;)V

    .line 136
    iget-object p1, p0, Lcom/phda/phserver/LockActivity;->submitBtn:Landroid/widget/Button;

    invoke-direct {p0}, Lcom/phda/phserver/LockActivity;->mp()Landroid/widget/LinearLayout$LayoutParams;

    move-result-object v10

    invoke-static {v10, v9}, Lcom/phda/phserver/LockActivity;->marginTop(Landroid/widget/LinearLayout$LayoutParams;I)Landroid/widget/LinearLayout$LayoutParams;

    move-result-object v9

    invoke-virtual {v2, p1, v9}, Landroid/widget/LinearLayout;->addView(Landroid/view/View;Landroid/view/ViewGroup$LayoutParams;)V

    .line 137
    iget-object p1, p0, Lcom/phda/phserver/LockActivity;->submitBtn:Landroid/widget/Button;

    new-instance v9, Lcom/phda/phserver/LockActivity$2;

    invoke-direct {v9, p0}, Lcom/phda/phserver/LockActivity$2;-><init>(Lcom/phda/phserver/LockActivity;)V

    invoke-virtual {p1, v9}, Landroid/widget/Button;->setOnClickListener(Landroid/view/View$OnClickListener;)V

    .line 141
    new-instance p1, Landroid/widget/TextView;

    invoke-direct {p1, p0}, Landroid/widget/TextView;-><init>(Landroid/content/Context;)V

    iput-object p1, p0, Lcom/phda/phserver/LockActivity;->status:Landroid/widget/TextView;

    .line 142
    iget-object p1, p0, Lcom/phda/phserver/LockActivity;->status:Landroid/widget/TextView;

    const-string v9, ""

    invoke-virtual {p1, v9}, Landroid/widget/TextView;->setText(Ljava/lang/CharSequence;)V

    .line 143
    iget-object p1, p0, Lcom/phda/phserver/LockActivity;->status:Landroid/widget/TextView;

    const/high16 v9, 0x41500000    # 13.0f

    invoke-virtual {p1, v6, v9}, Landroid/widget/TextView;->setTextSize(IF)V

    .line 144
    iget-object p1, p0, Lcom/phda/phserver/LockActivity;->status:Landroid/widget/TextView;

    invoke-virtual {p1, v5}, Landroid/widget/TextView;->setGravity(I)V

    .line 145
    iget-object p1, p0, Lcom/phda/phserver/LockActivity;->status:Landroid/widget/TextView;

    invoke-direct {p0}, Lcom/phda/phserver/LockActivity;->mp()Landroid/widget/LinearLayout$LayoutParams;

    move-result-object v9

    mul-int/lit8 v10, v0, 0x10

    invoke-static {v9, v10}, Lcom/phda/phserver/LockActivity;->marginTop(Landroid/widget/LinearLayout$LayoutParams;I)Landroid/widget/LinearLayout$LayoutParams;

    move-result-object v9

    invoke-virtual {v2, p1, v9}, Landroid/widget/LinearLayout;->addView(Landroid/view/View;Landroid/view/ViewGroup$LayoutParams;)V

    .line 148
    new-instance p1, Landroid/widget/Button;

    invoke-direct {p1, p0}, Landroid/widget/Button;-><init>(Landroid/content/Context;)V

    .line 149
    const-string v9, "CONFIGURA\u00c7\u00d5ES"

    invoke-virtual {p1, v9}, Landroid/widget/Button;->setText(Ljava/lang/CharSequence;)V

    .line 150
    invoke-virtual {p1, v4}, Landroid/widget/Button;->setAllCaps(Z)V

    .line 151
    invoke-virtual {p1, v7}, Landroid/widget/Button;->setTextColor(I)V

    .line 152
    new-instance v9, Landroid/graphics/drawable/GradientDrawable;

    invoke-direct {v9}, Landroid/graphics/drawable/GradientDrawable;-><init>()V

    .line 153
    invoke-virtual {v9, v4}, Landroid/graphics/drawable/GradientDrawable;->setColor(I)V

    .line 154
    mul-int/lit8 v0, v0, 0x2

    invoke-virtual {v9, v0, v7}, Landroid/graphics/drawable/GradientDrawable;->setStroke(II)V

    .line 155
    invoke-virtual {v9, v1}, Landroid/graphics/drawable/GradientDrawable;->setCornerRadius(F)V

    .line 156
    nop

    .line 157
    invoke-virtual {p1, v9}, Landroid/widget/Button;->setBackground(Landroid/graphics/drawable/Drawable;)V

    .line 161
    new-instance v0, Lcom/phda/phserver/LockActivity$3;

    invoke-direct {v0, p0}, Lcom/phda/phserver/LockActivity$3;-><init>(Lcom/phda/phserver/LockActivity;)V

    invoke-virtual {p1, v0}, Landroid/widget/Button;->setOnClickListener(Landroid/view/View$OnClickListener;)V

    .line 171
    invoke-direct {p0}, Lcom/phda/phserver/LockActivity;->mp()Landroid/widget/LinearLayout$LayoutParams;

    move-result-object v0

    invoke-static {v0, v10}, Lcom/phda/phserver/LockActivity;->marginTop(Landroid/widget/LinearLayout$LayoutParams;I)Landroid/widget/LinearLayout$LayoutParams;

    move-result-object v0

    invoke-virtual {v2, p1, v0}, Landroid/widget/LinearLayout;->addView(Landroid/view/View;Landroid/view/ViewGroup$LayoutParams;)V

    .line 173
    new-instance p1, Landroid/widget/TextView;

    invoke-direct {p1, p0}, Landroid/widget/TextView;-><init>(Landroid/content/Context;)V

    .line 174
    const-string v0, "Build mantida por PHDA"

    invoke-virtual {p1, v0}, Landroid/widget/TextView;->setText(Ljava/lang/CharSequence;)V

    .line 175
    invoke-virtual {p1, v8}, Landroid/widget/TextView;->setTextColor(I)V

    .line 176
    const/high16 v0, 0x41300000    # 11.0f

    invoke-virtual {p1, v6, v0}, Landroid/widget/TextView;->setTextSize(IF)V

    .line 177
    invoke-virtual {p1, v5}, Landroid/widget/TextView;->setGravity(I)V

    .line 178
    invoke-direct {p0}, Lcom/phda/phserver/LockActivity;->mp()Landroid/widget/LinearLayout$LayoutParams;

    move-result-object v0

    invoke-static {v0, v3}, Lcom/phda/phserver/LockActivity;->marginTop(Landroid/widget/LinearLayout$LayoutParams;I)Landroid/widget/LinearLayout$LayoutParams;

    move-result-object v0

    invoke-virtual {v2, p1, v0}, Landroid/widget/LinearLayout;->addView(Landroid/view/View;Landroid/view/ViewGroup$LayoutParams;)V

    .line 180
    invoke-virtual {p0, v2}, Lcom/phda/phserver/LockActivity;->setContentView(Landroid/view/View;)V

    .line 181
    invoke-virtual {p0}, Lcom/phda/phserver/LockActivity;->getWindow()Landroid/view/Window;

    move-result-object p1

    const/4 v0, 0x4

    invoke-virtual {p1, v0}, Landroid/view/Window;->setSoftInputMode(I)V

    .line 182
    iget-object p1, p0, Lcom/phda/phserver/LockActivity;->input:Landroid/widget/EditText;

    invoke-virtual {p1}, Landroid/widget/EditText;->requestFocus()Z

    .line 183
    return-void
.end method
