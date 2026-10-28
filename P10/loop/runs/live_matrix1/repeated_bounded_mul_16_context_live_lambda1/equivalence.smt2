; benchmark generated from python API
(set-info :status unknown)
(declare-fun c () (_ BitVec 16))
(declare-fun a () (_ BitVec 16))
(declare-fun b () (_ BitVec 16))
(assert
 (let ((?x9 (bvmul ((_ zero_extend 2) ((_ extract 2 0) ((_ extract 2 0) ((_ extract 2 0) b)))) ((_ zero_extend 3) ((_ extract 1 0) ((_ extract 15 0) a))))))
(let ((?x16 ((_ zero_extend 1) ((_ extract 4 0) ((_ zero_extend 11) ?x9)))))
(let ((?x82 ((_ extract 15 0) ((_ extract 15 0) ((_ extract 15 0) ((_ extract 15 0) ((_ extract 15 0) ((_ zero_extend 10) (bvadd ?x16 ?x16)))))))))
(let (($x255 (and (distinct (ite (bvult a (_ bv4 16)) (_ bv1 1) (_ bv0 1)) (_ bv0 1)) true)))
(let ((?x6 ((_ extract 15 0) (bvmul ((_ extract 15 0) a) ((_ zero_extend 13) ((_ extract 2 0) b))))))
(and (distinct (ite $x255 (bvadd ?x6 ?x6) c) (ite $x255 ((_ extract 15 0) ((_ extract 15 0) ?x82)) c)) true)))))))
(check-sat)
